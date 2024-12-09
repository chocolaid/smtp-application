#!/usr/bin/env python3

import os
import sys
import time
import random
import string
import traceback
from datetime import datetime
from threading import Thread
from time import sleep
from colorama import init, Fore, Style, Back
from src.utils.updater import Updater
from src.config.settings import Settings
from src.utils.helpers import ensure_directory

# Initialize colorama for cross-platform color support
init()

# Add project root to Python path
if getattr(sys, 'frozen', False):
    project_root = os.path.dirname(sys.executable)
else:
    project_root = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, project_root)

def clear_screen():
    """Clear the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def matrix_animation(duration=3):
    """Display Matrix-like animation for specified duration."""
    try:
        clear_screen()
        end_time = time.time() + duration
        while time.time() < end_time:
            # Generate random characters for matrix effect
            line = ''
            for _ in range(random.randint(20, 80)):
                char = random.choice(string.ascii_letters + string.digits + '!@#$%^&*()_+-=[]{}|;:,.<>?')
                line += f"{char} "
            print(f"{Fore.GREEN}{line}{Style.RESET_ALL}")
            sleep(0.05)
        clear_screen()
    except:
        pass

def menu_logo():
    """Display customized logo with author information."""
    # Rainbow colors
    colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
    
    # ASCII Art Logo
    logo = """
    ███████╗███╗   ███╗████████╗██████╗     ███╗   ███╗ █████╗ ███╗   ██╗ █████╗  ██████╗ ███████╗██████╗ 
    ██╔════╝████╗ ████║╚══██╔══╝██╔══██╗    ████╗ ████║██╔══██╗████╗  ██║██╔══██╗██╔════╝ ██╔════╝██╔══██╗
    ███████╗██╔████╔██║   ██║   ██████╔╝    ██╔████╔██║███████║██╔██╗ ██║███████║██║  ███╗█████╗  ██████╔╝
    ╚════██║██║╚██╔╝██║   ██║   ██╔═══╝     ██║╚██╔╝██║██╔══██║██║╚██╗██║██╔══██║██║   ██║██╔══╝  ██╔══██╗
    ███████║██║ ╚═╝ ██║   ██║   ██║         ██║ ╚═╝ ██║██║  ██║██║ ╚████║██║  ██║╚██████╔╝███████╗██║  ██║
    ╚══════╝╚═╝     ╚═╝   ╚═╝   ╚═╝         ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
    """
    
    # Author information
    author_info = [
        "╔════════════════════════════════════════════════════════════════╗",
        "║                  Created by:  OECAPPS                          ║",
        "║              Email: ebenedict291@gmail.com                     ║",
        "║     Message: Empowering Communication Through Technology       ║",
        "╚════════════════════════════════════════════════════════════════╝"
    ]
    
    # Print logo with random colors for each line
    print("\n")
    for line in logo.split('\n'):
        color = random.choice(colors)
        print(f"{color}{line}{Style.RESET_ALL}")
    
    # Print author information with random colors
    print("\n")
    for line in author_info:
        color = random.choice(colors)
        print(f"{color}{line}{Style.RESET_ALL}")
    print("\n")

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
        path = os.path.abspath(os.path.join(project_root, directory))
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
        create_directory_structure()
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
    """Get current version."""
    try:
        from src.config.version import VERSION
        return VERSION
    except:
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

        # Show matrix animation
        matrix_animation(3)
        
        # Show custom logo
        menu_logo()
        
        # Display banner
        display_banner()
        
        # Setup environment first
        if not setup_environment():
            print(f"{Fore.RED}Failed to setup environment. Exiting...{Style.RESET_ALL}")
            return

        # Check for updates
        if Settings.CHECK_UPDATES_ON_START:
            updater = Updater(Settings.GITHUB_TOKEN, Settings.GITHUB_REPO)
            update_result = updater.check_for_updates(mandatory=True)
            
            if update_result is None:  # Update was installed
                print(f"{Fore.GREEN}Update installed. Please restart the application.{Style.RESET_ALL}")
                return
            elif not update_result:  # Update failed
                print(f"{Fore.RED}Cannot continue without updating. Please try again.{Style.RESET_ALL}")
                return

        # Import the application class
        from src.app import SMTPApplication
        
        # Initialize and start application
        print(f"{Fore.CYAN}Initializing application...{Style.RESET_ALL}")
        app = SMTPApplication()
        app.start()

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Application terminated by user.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Fatal error: {str(e)}{Style.RESET_ALL}")
        traceback.print_exc()
    finally:
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()