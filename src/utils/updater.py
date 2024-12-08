import os
import sys
import shutil
import tempfile
import subprocess
from git import Repo
from packaging import version
import json
from Cython.Build import cythonize
from setuptools import setup
from src.utils.logger import Logger
from src.config.settings import Settings

class Updater:
    def __init__(self, github_token: str, repo_url: str):
        self.logger = Logger()
        self.github_token = github_token
        self.repo_url = repo_url
        self.temp_dir = tempfile.mkdtemp()
        self.current_version = self._get_current_version()

    def _get_current_version(self) -> str:
        """Get current version from version.json"""
        try:
            with open('version.json', 'r') as f:
                return json.load(f)['version']
        except:
            return "0.0.0"

    def _get_remote_version(self) -> str:
        """Get version from remote repository"""
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

    def _build_exe(self):
        """Build the application using Cython and PyInstaller"""
        try:
            # Change to temp directory
            os.chdir(self.temp_dir)

            # Cythonize Python files
            python_files = []
            for root, _, files in os.walk('src'):
                for file in files:
                    if file.endswith('.py'):
                        python_files.append(os.path.join(root, file))

            setup(
                ext_modules=cythonize(python_files),
                script_args=['build_ext', '--inplace']
            )

            # Create PyInstaller command
            pyinstaller_cmd = [
                'pyinstaller',
                '--onefile',
                '--noconsole',
                '--name', 'smtp_manager',
                'main.py'
            ]

            # Run PyInstaller
            subprocess.run(pyinstaller_cmd, check=True)
            
            return os.path.join('dist', 'smtp_manager.exe')

        except Exception as e:
            self.logger.error(f"Error building executable: {str(e)}")
            return None

    def _replace_executable(self, new_exe_path: str):
        """Replace current executable with new version"""
        try:
            current_exe = sys.executable
            temp_backup = current_exe + '.backup'

            # Create backup of current executable
            shutil.copy2(current_exe, temp_backup)

            try:
                # Replace executable
                shutil.copy2(new_exe_path, current_exe)
                os.remove(temp_backup)
                return True
            except Exception as e:
                # Restore backup if replacement fails
                shutil.copy2(temp_backup, current_exe)
                os.remove(temp_backup)
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
                new_exe = self._build_exe()
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
                shutil.rmtree(self.temp_dir)
            except:
                pass