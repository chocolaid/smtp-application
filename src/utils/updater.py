import os
import sys
import json
import shutil
import tempfile
import platform
import subprocess
from git import Repo
from packaging import version
from datetime import datetime
from colorama import Fore, Style
from src.utils.logger import Logger
from src.config.settings import Settings

class Updater:
    def __init__(self, github_token: str, repo_url: str):
        self.logger = Logger()
        self.github_token = github_token
        self.repo_url = repo_url
        self.temp_dir = tempfile.mkdtemp()
        self.current_version = self._get_current_version()
        self.platform = platform.system().lower()
        self.build_dir = None
        self.is_admin = self._check_admin()
        self.exe_name = 'smtp_manager.exe' if self.platform == 'windows' else 'smtp_manager'

    def _is_running_from_source(self):
        """Check if running from source code or built executable"""
        return os.path.basename(sys.executable) in ['python.exe', 'python', 'python3']

    def _check_admin(self):
        """Check if the application has admin privileges"""
        try:
            if self.platform == 'windows':
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            elif self.platform == 'darwin':  # macOS
                return os.getuid() == 0
            else:  # Linux and others
                return os.geteuid() == 0
        except:
            return False

    def _run_as_admin(self):
        """Restart the application with admin privileges"""
        try:
            if self.platform == 'windows':
                import ctypes
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
            elif self.platform == 'darwin':  # macOS
                script = f'''
                do shell script "{sys.executable} {' '.join(sys.argv)}" with administrator privileges
                '''
                subprocess.run(['osascript', '-e', script])
            else:  # Linux and others
                if shutil.which('sudo'):
                    os.execvp('sudo', ['sudo', sys.executable] + sys.argv)
                else:
                    raise Exception("sudo is not available")
            sys.exit(0)
        except Exception as e:
            self.logger.error(f"Failed to gain admin privileges: {str(e)}")
            return False
    def _get_current_version(self) -> str:
        """Get current version from embedded version info"""
        return "8.0.0" 

    def _get_remote_version(self) -> str:
        """Get version from remote repository's src/config/version.py"""
        try:
            # Clone with authentication
            auth_url = self.repo_url.replace('https://', f'https://{self.github_token}@')
            repo = Repo.clone_from(auth_url, self.temp_dir, depth=1)
            
            version_file = os.path.join(self.temp_dir, 'src', 'config', 'version.py')
            if os.path.exists(version_file):
                with open(version_file, 'r') as f:
                    version_content = f.read()
                    # Extract version using simple string parsing
                    version_line = [line for line in version_content.split('\n') if 'VERSION =' in line][0]
                    return version_line.split('=')[1].strip().strip('"\'')
            raise Exception("version.py not found in repository")
                
        except Exception as e:
            self.logger.error(f"Error checking remote version: {str(e)}")
            return "0.0.0"

    def _prepare_build_directory(self):
        """Prepare the build directory with necessary files"""
        try:
            # Create build directory
            self.build_dir = os.path.join(self.temp_dir, 'build')
            os.makedirs(self.build_dir, exist_ok=True)

            data_dirs = [
                'data',
                'data/smtp',
                'data/templates',
                'data/recipients',
                'data/campaigns',
                'data/backups',
                'data/logs'
            ]
        
            for dir_path in data_dirs:
                os.makedirs(os.path.join(self.build_dir, dir_path), exist_ok=True)

            # Copy source files
            shutil.copytree(
                os.path.join(self.temp_dir, 'src'),
                os.path.join(self.build_dir, 'src'),
                dirs_exist_ok=True
            )

            # Copy main script
            shutil.copy2(
                os.path.join(self.temp_dir, 'main.py'),
                os.path.join(self.build_dir, 'main.py')
            )

            # Copy version file
            shutil.copy2(
                os.path.join(self.temp_dir, 'version.json'),
                os.path.join(self.build_dir, 'version.json')
            )

            # Copy assets if they exist
            assets_dir = os.path.join(self.temp_dir, 'assets')
            if os.path.exists(assets_dir):
                shutil.copytree(
                    assets_dir,
                    os.path.join(self.build_dir, 'assets'),
                    dirs_exist_ok=True
                )

            return True

        except Exception as e:
            self.logger.error(f"Error preparing build directory: {str(e)}")
            return False

    def _create_setup_script(self):
        """Create setup.py for cx_Freeze"""
        setup_script = """
import sys
from cx_Freeze import setup, Executable

# Minimal build options to reduce complexity
build_exe_options = {
    "packages": ["src"],
    "excludes": ["tkinter", "test", "unittest"],
    "include_files": [
        ("data", "data"),
        ("assets", "assets")
    ],
    "build_exe": "build/SMTP Manager"
}

base = "Console" if sys.platform == "win32" else None

setup(
    name = "SMTP Manager",
    version = "%s",
    description = "SMTP Manager",
    options = {"build_exe": build_exe_options},
    executables = [Executable(
        "main.py",
        base=base,
        target_name="%s"
    )]
)
""" % (self.current_version, self.exe_name)

        setup_path = os.path.join(self.build_dir, "setup.py")
        with open(setup_path, "w") as f:
            f.write(setup_script)
        return setup_path
    
    
    def _build_windows(self):
        """Build for Windows using cx_Freeze"""
        try:
            setup_path = self._create_setup_script()
            
            # Create and activate a virtual environment for building
            venv_path = os.path.join(self.temp_dir, 'venv')
            subprocess.run([sys.executable, '-m', 'venv', venv_path], check=True)
            
            # Get path to venv Python executable
            venv_python = os.path.join(venv_path, 'Scripts', 'python.exe')
            
            # Install required packages in venv
            subprocess.run([
                venv_python, '-m', 'pip', 'install', 
                'cx_Freeze',
                'colorama',
                'cryptography',
                'GitPython',
                'packaging'
            ], check=True)
            
            # Set higher recursion limit
            sys.setrecursionlimit(5000)
            
            # Add more detailed error output
            result = subprocess.run(
                [venv_python, setup_path, "build"],
                cwd=self.build_dir,
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    'PYTHONPATH': self.build_dir,
                    'VIRTUAL_ENV': venv_path,
                    'PATH': f"{os.path.join(venv_path, 'Scripts')}{os.pathsep}{os.environ['PATH']}"
                }
            )
            
            if result.returncode != 0:
                self.logger.error(f"Build output:\n{result.stdout}\n{result.stderr}")
                raise Exception(f"Build failed with return code {result.returncode}")
                
            # Find the built executable
            for root, _, files in os.walk(os.path.join(self.build_dir, "build")):
                for file in files:
                    if file == self.exe_name:
                        return os.path.join(root, file)
            
            raise Exception("Built executable not found")
        except Exception as e:
            self.logger.error(f"Windows build failed: {str(e)}")
            return None
    def _build_macos(self):
        """Build for macOS using cx_Freeze"""
        try:
            setup_path = self._create_setup_script()
            subprocess.run([
                sys.executable,
                setup_path,
                "build"
            ], cwd=self.build_dir, check=True)
            
            # Find the built executable
            for root, _, files in os.walk(os.path.join(self.build_dir, "build")):
                for file in files:
                    if file == self.exe_name:
                        exe_path = os.path.join(root, file)
                        os.chmod(exe_path, 0o755)
                        return exe_path
            
            raise Exception("Built executable not found")
        except Exception as e:
            self.logger.error(f"macOS build failed: {str(e)}")
            return None

    def _build_linux(self):
        """Build for Linux using cx_Freeze"""
        try:
            setup_path = self._create_setup_script()
            subprocess.run([
                sys.executable,
                setup_path,
                "build"
            ], cwd=self.build_dir, check=True)
            
            # Find the built executable
            for root, _, files in os.walk(os.path.join(self.build_dir, "build")):
                for file in files:
                    if file == self.exe_name:
                        exe_path = os.path.join(root, file)
                        os.chmod(exe_path, 0o755)
                        return exe_path
            
            raise Exception("Built executable not found")
        except Exception as e:
            self.logger.error(f"Linux build failed: {str(e)}")
            return None

    def _build_executable(self):
        """Build executable for current platform"""
        try:
            # Get the absolute path to the project root
            current_file = os.path.abspath(__file__)  # Gets path to updater.py
            utils_dir = os.path.dirname(current_file)  # Gets path to utils directory
            src_dir = os.path.dirname(utils_dir)      # Gets path to src directory
            project_root = os.path.dirname(src_dir)    # Gets path to project root
            
            # Add to Python path
            sys.path.insert(0, project_root)
            
            if not self._prepare_build_directory():
                raise Exception("Failed to prepare build directory")
                
            build_functions = {
                'windows': self._build_windows,
                'darwin': self._build_macos,
                'linux': self._build_linux
            }
            
            build_func = build_functions.get(self.platform)
            if not build_func:
                raise Exception(f"Unsupported platform: {self.platform}")
                
            return build_func()
            
        except Exception as e:
            self.logger.error(f"Build failed: {str(e)}")
            return None
        
    
    def _copy_required_files(self, install_dir):
        """Copy required files and directories to installation directory"""
        try:
            # Copy data directory structure
            data_dirs = ['smtp', 'templates', 'recipients', 'campaigns', 'logs', 'backups']
            for dir_name in data_dirs:
                os.makedirs(os.path.join(install_dir, 'data', dir_name), exist_ok=True)

            # Copy version.json
            shutil.copy2(
                os.path.join(self.build_dir, 'version.json'),
                os.path.join(install_dir, 'version.json')
            )

            # Copy assets if they exist
            assets_dir = os.path.join(self.build_dir, 'assets')
            if os.path.exists(assets_dir):
                shutil.copytree(
                    assets_dir,
                    os.path.join(install_dir, 'assets'),
                    dirs_exist_ok=True
                )

            # Create a README file
            readme_content = f"""SMTP Manager
Version: {self.current_version}
Installation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

To run the application:
{self.exe_name}

Note: Do not delete any files in this directory."""

            with open(os.path.join(install_dir, 'README.txt'), 'w') as f:
                f.write(readme_content)

        except Exception as e:
            self.logger.error(f"Error copying required files: {str(e)}")
            raise

    def _replace_executable(self, new_path: str):
        """Replace current executable with new version"""
        try:
            if self._is_running_from_source():
                print(f"{Fore.YELLOW}Running from source code. Installing built version...{Style.RESET_ALL}")
                
                # Get desktop path based on platform
                if self.platform == 'windows':
                    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
                elif self.platform == 'darwin':  # macOS
                    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
                else:  # Linux
                    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
                    # Fallback to home directory if Desktop doesn't exist
                    if not os.path.exists(desktop_path):
                        desktop_path = os.path.expanduser('~')
                
                # Create application directory on desktop
                install_dir = os.path.join(desktop_path, 'SMTPManager')
                os.makedirs(install_dir, exist_ok=True)
                
                target_path = os.path.join(install_dir, self.exe_name)
                
                # Copy the new executable and required files
                shutil.copy2(new_path, target_path)
                self._copy_required_files(install_dir)
                
                # Set proper permissions
                if self.platform != 'windows':
                    os.chmod(target_path, 0o755)
                
                print(f"{Fore.GREEN}Application installed to: {target_path}")
                print(f"Please run the application from that location next time.{Style.RESET_ALL}")
                return True
                
            else:
                current_path = sys.executable
                backup_path = current_path + '.backup'
                
                if not self._check_file_permissions(current_path):
                    if not self.is_admin:
                        print(f"{Fore.YELLOW}Admin privileges required for update. Requesting elevation...{Style.RESET_ALL}")
                        return self._run_as_admin()
                
                shutil.copy2(current_path, backup_path)
                
                try:
                    if self.platform == 'darwin':
                        app_name = os.path.basename(current_path)
                        subprocess.run(['pkill', '-f', app_name], stderr=subprocess.DEVNULL)
                        shutil.copy2(new_path, current_path)
                        os.chmod(current_path, 0o755)
                    elif self.platform == 'windows':
                        import win32api
                        import win32con
                        win32api.SetFileAttributes(current_path, win32con.FILE_ATTRIBUTE_NORMAL)
                        os.replace(new_path, current_path)
                    else:
                        shutil.copy2(new_path, current_path)
                        os.chmod(current_path, 0o755)
                    
                    os.remove(backup_path)
                    return True
                    
                except Exception as e:
                    if os.path.exists(backup_path):
                        shutil.copy2(backup_path, current_path)
                        os.remove(backup_path)
                    raise e

        except Exception as e:
            self.logger.error(f"Error replacing executable: {str(e)}")
            return False

    def check_for_updates(self, mandatory=True) -> bool:
        """Check for updates and install if available"""
        try:
            remote_version = self._get_remote_version()
            
            if version.parse(remote_version) > version.parse(self.current_version):
                print(f"{Fore.YELLOW}Update required: v{self.current_version} → v{remote_version}{Style.RESET_ALL}")
                
                print(f"{Fore.CYAN}Building new version... This may take a few minutes.{Style.RESET_ALL}")
                new_exe = self._build_executable()
                if not new_exe:
                    raise Exception("Failed to build new version")

                print(f"{Fore.CYAN}Installing update...{Style.RESET_ALL}")
                if self._replace_executable(new_exe):
                    if self._is_running_from_source():
                        return True  # Continue running from source this time
                    print(f"{Fore.GREEN}Update installed successfully. The application will now exit.{Style.RESET_ALL}")
                    sys.exit(0)  # Exit immediately after successful update
                else:
                    raise Exception("Failed to replace executable")

            else:
                print(f"{Fore.GREEN}You are running the latest version: v{self.current_version}{Style.RESET_ALL}")
                return True

        except Exception as e:
            error_msg = f"Update failed: {str(e)}"
            self.logger.error(error_msg)
            if mandatory:
                print(f"{Fore.RED}{error_msg}")
                print(f"Updates are required to run this application.{Style.RESET_ALL}")
                return False
            return False