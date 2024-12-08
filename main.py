#!/usr/bin/env python3

import os
import sys
import traceback
from datetime import datetime
from colorama import init, Fore, Style
from src.utils.updater import Updater
from src.config.settings import Settings
from src.utils.helpers import ensure_directory

# Initialize colorama for cross-platform color support
init()

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def create_directory_structure():
    """Create the application directory structure."""
    directories = [
        'data',
        'data/smtp',
        'data/templates',
        'data/recipients',
        'data/campaigns',
        'data/backups',
        'data/logs',
        'src/managers',
        'src/utils',
        'src/config'
    ]
    
    for directory in directories:
        path = os.path.join(project_root, directory)
        os.makedirs(path, exist_ok=True)

def create_init_files():
    """Create __init__.py files in all necessary directories."""
    init_directories = [
        'src',
        'src/managers',
        'src/utils',
        'src/config'
    ]
    
    for directory in init_directories:
        init_file = os.path.join(project_root, directory, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write('# Package initialization\n')

def setup_environment():
    """Setup the application environment."""
    try:
        # Create necessary directories
        create_directory_structure()
        
        # Create __init__.py files
        create_init_files()
        
        # Ensure data directories exist
        ensure_directory(Settings.DATA_DIR)
        ensure_directory(Settings.SMTP_DIR)
        ensure_directory(Settings.TEMPLATES_DIR)
        ensure_directory(Settings.RECIPIENTS_DIR)
        ensure_directory(Settings.LOGS_DIR)
        ensure_directory(Settings.BACKUPS_DIR)
        
        return True
        
    except Exception as e:
        print(f"{Fore.RED}Error setting up environment: {str(e)}{Style.RESET_ALL}")
        return False

def display_banner():
    """Display application banner."""
    banner = f"""
    {Fore.CYAN}╔══════════════════════════════════════════╗
    ║             SMTP Manager                  ║
    ║        Version: {get_version()}              ║
    ╚══════════════════════════════════════════╝{Style.RESET_ALL}
    """
    print(banner)

def get_version():
    """Get current version from version.json."""
    try:
        version_file = os.path.join(project_root, 'version.json')
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                import json
                data = json.load(f)
                return data.get('version', '1.0.0')
    except:
        pass
    return '1.0.0'

def check_python_version():
    """Check if Python version meets requirements."""
    if sys.version_info < (3, 7):
        print(f"{Fore.RED}Error: Python 3.7 or higher is required.{Style.RESET_ALL}")
        return False
    return True

def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = [
        'colorama',
        'cryptography',
        'gitpython',
        'cx_freeze'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"{Fore.RED}Missing required packages: {', '.join(missing_packages)}")
        print(f"Please install them using: pip install {' '.join(missing_packages)}{Style.RESET_ALL}")
        return False
    return True

def main():
    try:
        # Check Python version
        if not check_python_version():
            return

        # Check dependencies
        if not check_dependencies():
            return

        # Import the application class
        from src.app import SMTPApplication
        
        # Display banner
        display_banner()
        
        # Check for updates if enabled
        if Settings.CHECK_UPDATES_ON_START:
            print(f"{Fore.CYAN}Checking for updates...{Style.RESET_ALL}")
            updater = Updater(Settings.GITHUB_TOKEN, Settings.GITHUB_REPO)
            if updater.check_for_updates():
                print(f"{Fore.GREEN}Update installed. Please restart the application.{Style.RESET_ALL}")
                return

        # Setup environment
        if not setup_environment():
            print(f"{Fore.RED}Failed to setup environment. Exiting...{Style.RESET_ALL}")
            return

        # Initialize and start application
        print(f"{Fore.CYAN}Initializing application...{Style.RESET_ALL}")
        app = SMTPApplication()
        app.run()

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Application terminated by user.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Fatal error: {str(e)}{Style.RESET_ALL}")
        traceback.print_exc()
    finally:
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()