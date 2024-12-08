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
                        return os.path.join(root, file)
            
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
                        return os.path.join(root, file)
            
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

    def _replace_executable(self, new_path: str):
        """Replace current executable with new version"""
        try:
            current_path = sys.executable
            backup_path = current_path + '.backup'
            
            # Create backup of current executable
            shutil.copy2(current_path, backup_path)
            
            try:
                # Replace executable
                shutil.copy2(new_path, current_path)
                os.remove(backup_path)
                return True
            except Exception as e:
                # Restore backup if replacement fails
                shutil.copy2(backup_path, current_path)
                os.remove(backup_path)
                raise e

        except Exception as e:
            self.logger.error(f"Error replacing executable: {str(e)}")
            return False

    def check_for_updates(self) -> bool:
        """Check for updates and install if available"""
        try:
            remote_version = self._get_remote_version()
            
            if version.parse(remote_version) > version.parse(self.current_version):
                self.logger.info(f"Update available: {remote_version}")
                
                # Build new version
                new_exe = self._build_executable()
                if not new_exe:
                    raise Exception("Failed to build new version")

                # Replace current executable
                if self._replace_executable(new_exe):
                    self.logger.info("Update installed successfully")
                    return True
                else:
                    raise Exception("Failed to replace executable")

            else:
                self.logger.info("No updates available")
                return False

        except Exception as e:
            self.logger.error(f"Update failed: {str(e)}")
            return False

        finally:
            # Cleanup
            try:
                if self.temp_dir and os.path.exists(self.temp_dir):
                    shutil.rmtree(self.temp_dir)
            except:
                pass