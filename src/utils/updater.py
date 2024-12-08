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
        """Get current version from version.json"""
        try:
            version_file = os.path.join(os.getcwd(), 'version.json')
            if os.path.exists(version_file):
                with open(version_file, 'r') as f:
                    return json.load(f)['version']
        except Exception as e:
            self.logger.error(f"Error reading version file: {str(e)}")
        return "0.0.0"

    def _get_remote_version(self) -> str:
        """Get version from remote repository"""
        try:
            # Clone with authentication
            auth_url = self.repo_url.replace('https://', f'https://{self.github_token}@')
            repo = Repo.clone_from(auth_url, self.temp_dir, depth=1)
            
            version_file = os.path.join(self.temp_dir, 'version.json')
            if os.path.exists(version_file):
                with open(version_file, 'r') as f:
                    return json.load(f)['version']
            raise Exception("version.json not found in repository")
            
        except Exception as e:
            self.logger.error(f"Error checking remote version: {str(e)}")
            return "0.0.0"

    def _prepare_build_directory(self):
        """Prepare the build directory with necessary files"""
        try:
            # Create build directory
            self.build_dir = os.path.join(self.temp_dir, 'build')
            os.makedirs(self.build_dir, exist_ok=True)

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

            # Create data directory structure
            data_dirs = ['smtp', 'templates', 'recipients', 'campaigns', 'logs', 'backups']
            for dir_name in data_dirs:
                os.makedirs(os.path.join(self.build_dir, 'data', dir_name), exist_ok=True)

            return True

        except Exception as e:
            self.logger.error(f"Error preparing build directory: {str(e)}")
            return False

    def _create_setup_script(self):
        """Create setup.py for cx_Freeze"""
        setup_script = """
import sys
from cx_Freeze import setup, Executable

# Dependencies
build_exe_options = {
    "packages": [
        "os", "sys", "json", "logging", "colorama", "cryptography",
        "datetime", "tempfile", "shutil", "platform", "subprocess",
        "git", "packaging"
    ],
    "excludes": ["tkinter", "test", "distutils"],
    "include_files": [
        ("src", "src"),
        ("data", "data"),
        ("version.json", "version.json")
    ]
}

# Base for GUI applications
base = None
if sys.platform == "win32":
    base = "Win32GUI"

# Target executable
target = Executable(
    script="main.py",
    base=base,
    target_name="smtp_manager" + (".exe" if sys.platform == "win32" else ""),
    icon="%s" if sys.platform == "win32" else None
)

setup(
    name="SMTP Manager",
    version="%s",
    description="SMTP Management Tool",
    options={"build_exe": build_exe_options},
    executables=[target]
)
""" % (Settings.APP_ICON_PATH, self.current_version)

        setup_path = os.path.join(self.build_dir, "setup.py")
        with open(setup_path, "w") as f:
            f.write(setup_script)
        return setup_path

    def _build_windows(self):
        """Build for Windows using cx_Freeze"""
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
                    if file == "smtp_manager.exe":
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
                    if file == "smtp_manager":
                        exe_path = os.path.join(root, file)
                        # Set proper permissions
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
                    if file == "smtp_manager":
                        exe_path = os.path.join(root, file)
                        # Set proper permissions
                        os.chmod(exe_path, 0o755)
                        return exe_path
            
            raise Exception("Built executable not found")
        except Exception as e:
            self.logger.error(f"Linux build failed: {str(e)}")
            return None

    def _build_executable(self):
        """Build executable for current platform"""
        try:
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

    def _check_file_permissions(self, path):
        """Check if we have write permissions for the file"""
        if not os.path.exists(path):
            return os.access(os.path.dirname(path), os.W_OK)
        return os.access(path, os.W_OK)

    def _replace_executable(self, new_path: str):
        """Replace current executable with new version"""
        try:
            current_path = sys.executable
            backup_path = current_path + '.backup'
            
            # Check if we need admin privileges
            if not self._check_file_permissions(current_path):
                if not self.is_admin:
                    print(f"{Fore.YELLOW}Admin privileges required for update. Requesting elevation...{Style.RESET_ALL}")
                    return self._run_as_admin()
            
            # Create backup of current executable
            shutil.copy2(current_path, backup_path)
            
            try:
                if self.platform == 'darwin':  # macOS
                    # Stop the current process if it's running
                    app_name = os.path.basename(current_path)
                    subprocess.run(['pkill', '-f', app_name], stderr=subprocess.DEVNULL)
                    
                    # Copy new executable
                    shutil.copy2(new_path, current_path)
                    # Set proper permissions
                    os.chmod(current_path, 0o755)
                    
                elif self.platform == 'windows':
                    import win32api
                    import win32con
                    # Set file attributes to normal
                    win32api.SetFileAttributes(current_path, win32con.FILE_ATTRIBUTE_NORMAL)
                    # Move new file to replace old one
                    os.replace(new_path, current_path)
                else:  # Linux
                    shutil.copy2(new_path, current_path)
                    os.chmod(current_path, 0o755)
                
                os.remove(backup_path)
                return True
                
            except Exception as e:
                # Restore backup if replacement fails
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
            print(f"{Fore.CYAN}Checking for updates...{Style.RESET_ALL}")
            remote_version = self._get_remote_version()
            
            if version.parse(remote_version) > version.parse(self.current_version):
                print(f"{Fore.YELLOW}Update required: v{self.current_version} → v{remote_version}{Style.RESET_ALL}")
                
                # Build new version
                print(f"{Fore.CYAN}Building new version...{Style.RESET_ALL}")
                new_exe = self._build_executable()
                if not new_exe:
                    raise Exception("Failed to build new version")

                # Replace current executable
                print(f"{Fore.CYAN}Installing update...{Style.RESET_ALL}")
                if self._replace_executable(new_exe):
                    print(f"{Fore.GREEN}Update installed successfully. Please restart the application.{Style.RESET_ALL}")
                    sys.exit(0)
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
                print("Updates are required to run this application.{Style.RESET_ALL}")
                sys.exit(1)
            return False

        finally:
            # Cleanup
            try:
                if self.temp_dir and os.path.exists(self.temp_dir):
                    shutil.rmtree(self.temp_dir)
            except:
                pass