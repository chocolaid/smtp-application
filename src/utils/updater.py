import os
import sys
import shutil
import tempfile
import subprocess
import platform
from git import Repo
from packaging import version
import json
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

    def _get_current_version(self) -> str:
        try:
            with open('version.json', 'r') as f:
                return json.load(f)['version']
        except:
            return "0.0.0"

    def _get_remote_version(self) -> str:
        try:
            repo = Repo.clone_from(
                self.repo_url.replace('https://', f'https://{self.github_token}@'),
                self.temp_dir,
                depth=1
            )
            with open(os.path.join(self.temp_dir, 'version.json'), 'r') as f:
                return json.load(f)['version']
        except Exception as e:
            self.logger.error(f"Error checking remote version: {str(e)}")
            return "0.0.0"

    def _create_setup_script(self):
        """Create setup.py for cx_Freeze"""
        setup_script = """
import sys
from cx_Freeze import setup, Executable

# Dependencies
build_exe_options = {
    "packages": ["os", "sys", "colorama", "cryptography", "logging"],
    "excludes": ["tkinter", "test", "distutils"],
    "include_files": [
        "version.json",
        "README.md",
        ("data", "data")
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
    target_name="smtp_manager",
    icon="assets/icon.ico"  # Make sure this path exists
)

setup(
    name="SMTP Manager",
    version="%s",
    description="SMTP Management Tool",
    options={"build_exe": build_exe_options},
    executables=[target]
)
""" % self.current_version

        setup_path = os.path.join(self.temp_dir, "setup.py")
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
            ], check=True)
            
            # Find the built executable
            build_dir = os.path.join(self.temp_dir, "build")
            for root, _, files in os.walk(build_dir):
                for file in files:
                    if file.endswith("smtp_manager.exe"):
                        return os.path.join(root, file)
            
            raise Exception("Built executable not found")
        except Exception as e:
            self.logger.error(f"Windows build failed: {str(e)}")
            return None

    def _build_macos(self):
        """Build for macOS using cx_Freeze and Platypus"""
        try:
            # First build with cx_Freeze
            setup_path = self._create_setup_script()
            subprocess.run([
                sys.executable,
                setup_path,
                "build"
            ], check=True)

            # Find the built executable
            build_dir = os.path.join(self.temp_dir, "build")
            exe_path = None
            for root, _, files in os.walk(build_dir):
                for file in files:
                    if file == "smtp_manager":
                        exe_path = os.path.join(root, file)
                        break

            if not exe_path:
                raise Exception("Built executable not found")

            # Create .app bundle using Platypus
            app_path = os.path.join(self.temp_dir, "SMTP Manager.app")
            subprocess.run([
                "platypus",
                "-a", "SMTP Manager",
                "-o", "None",
                "-i", "assets/icon.icns",  # Make sure this exists
                "-V", self.current_version,
                "-u", "OECAPPS",
                "-I", "oec.apps.smtpmanager",
                "-c", exe_path,
                app_path
            ], check=True)

            return app_path

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
            ], check=True)
            
            # Find the built executable
            build_dir = os.path.join(self.temp_dir, "build")
            for root, _, files in os.walk(build_dir):
                for file in files:
                    if file == "smtp_manager":
                        return os.path.join(root, file)
            
            raise Exception("Built executable not found")
        except Exception as e:
            self.logger.error(f"Linux build failed: {str(e)}")
            return None

    def _build_executable(self):
        """Build executable for current platform"""
        build_functions = {
            'windows': self._build_windows,
            'darwin': self._build_macos,
            'linux': self._build_linux
        }
        
        build_func = build_functions.get(self.platform)
        if not build_func:
            raise Exception(f"Unsupported platform: {self.platform}")
            
        return build_func()

    def _replace_executable(self, new_path: str):
        """Replace current executable with new version"""
        try:
            current_path = sys.executable
            if self.platform == 'darwin':
                # For macOS, replace the entire .app bundle
                current_app = os.path.dirname(os.path.dirname(os.path.dirname(current_path)))
                backup_path = current_app + '.backup'
                shutil.move(current_app, backup_path)
                try:
                    shutil.copytree(new_path, current_app)
                    shutil.rmtree(backup_path)
                    return True
                except Exception as e:
                    shutil.move(backup_path, current_app)
                    raise e
            else:
                # For Windows and Linux
                backup_path = current_path + '.backup'
                shutil.copy2(current_path, backup_path)
                try:
                    shutil.copy2(new_path, current_path)
                    os.remove(backup_path)
                    return True
                except Exception as e:
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
                new_path = self._build_executable()
                if not new_path:
                    raise Exception("Failed to build new version")

                # Replace current executable
                if self._replace_executable(new_path):
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
                shutil.rmtree(self.temp_dir)
            except:
                pass