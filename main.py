#!/usr/bin/env python3

import os
import sys
import traceback
from datetime import datetime
from colorama import init, Fore, Style
from src.utils.updater import Updater
from src.config.settings import Settings


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
        # Create directory structure
        create_directory_structure()
        
        # Create __init__.py files
        create_init_files()

        # Set up environment variables
        os.environ['SMTP_APP_ENV'] = os.getenv('SMTP_APP_ENV', 'production')
        os.environ['SMTP_APP_ROOT'] = project_root
        
        # Set up logging directory
        log_file = os.path.join(project_root, 'data', 'logs', 'smtp_manager.log')
        os.environ['SMTP_APP_LOG'] = log_file
        
        return True
    except Exception as e:
        print(f"{Fore.RED}Failed to setup environment: {str(e)}{Style.RESET_ALL}")
        return False

def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = {
        'colorama': 'For colored terminal output',
        'cryptography': 'For encryption and security features',
        'bs4': 'For HTML template processing',
        'pandas': 'For data handling and Excel support',
        'schedule': 'For campaign scheduling',
        'openpyxl': 'For Excel file support',
        'requests': 'For external API interactions',
        'dateutil': 'For date handling',
        'tqdm': 'For progress bars'
    }
    
    missing_packages = {}
    
    for package, description in required_packages.items():
        try:
            __import__(package)
        except ImportError:
            missing_packages[package] = description
    
    return missing_packages

def setup_exception_handling():
    """Setup global exception handling."""
    def global_exception_handler(exctype, value, tb):
        """Handle uncaught exceptions."""
        error_msg = ''.join(traceback.format_exception(exctype, value, tb))
        
        # Log the error
        error_log_path = os.path.join(project_root, 'data', 'logs', 'errors.log')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            with open(error_log_path, 'a') as f:
                f.write(f"\n[{timestamp}] Uncaught Exception:\n{error_msg}\n")
        except:
            pass  # If we can't write to the log file, continue to display the error
        
        # Display error to user
        print(f"\n{Fore.RED}An unexpected error occurred:{Style.RESET_ALL}")
        print(f"{Fore.RED}{str(value)}{Style.RESET_ALL}")
        print("\nThis error has been logged. Press Enter to exit...")
        input()
        sys.exit(1)
    
    sys.excepthook = global_exception_handler

def display_startup_banner():
    """Display the application startup banner."""
    version = "1.0.0"
    python_version = sys.version.split()[0]
    
    banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════╗
║                   SMTP Manager v{version}                   ║
║            Secure Email Campaign Management            ║
╠══════════════════════════════════════════════════════╣
║  Python {python_version}  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}  ║
╚══════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)

def check_python_version():
    """Check if Python version meets requirements."""
    required_version = (3, 7)
    current_version = sys.version_info[:2]
    
    if current_version < required_version:
        print(f"{Fore.RED}Error: Python {required_version[0]}.{required_version[1]} or higher is required.")
        print(f"Current version: Python {current_version[0]}.{current_version[1]}{Style.RESET_ALL}")
        return False
    return True

def main():
    """Main application entry point."""

    try:
        # Check for updates if enabled
        if Settings.CHECK_UPDATES_ON_START:
            updater = Updater(Settings.GITHUB_TOKEN, Settings.GITHUB_REPO)
            if updater.check_for_updates():
                print(f"{Fore.GREEN}Update installed. Please restart the application.{Style.RESET_ALL}")
                return

        # Continue with normal application startup
        create_directory_structure()
        create_init_files()
        
        app = SMTPApplication()
        app.run()

    except Exception as e:
        print(f"{Fore.RED}Fatal error: {str(e)}{Style.RESET_ALL}")
        traceback.print_exc()
        input("\nPress Enter to exit...")

    try:
        # Display startup banner
        display_startup_banner()
        
        # Check Python version
        if not check_python_version():
            sys.exit(1)

        # Check dependencies
        missing_packages = check_dependencies()
        if missing_packages:
            print(f"{Fore.RED}Error: Missing required packages:{Style.RESET_ALL}")
            print("\nPlease install the following packages:")
            for package, description in missing_packages.items():
                print(f"  - {package}: {description}")
            print("\nYou can install them using:")
            print(f"pip install {' '.join(missing_packages.keys())}")
            sys.exit(1)

        # Setup environment
        if not setup_environment():
            sys.exit(1)

        # Setup exception handling
        setup_exception_handling()

        print(f"{Fore.GREEN}Environment setup completed successfully.{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Initializing application...{Style.RESET_ALL}")

        # Import and initialize the application
        from src.app import SMTPApplication
        
        app = SMTPApplication()
        app.start()

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Application terminated by user.{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}Fatal Error: {str(e)}{Style.RESET_ALL}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        print(f"\n{Fore.CYAN}Thank you for using SMTP Manager!{Style.RESET_ALL}")

if __name__ == "__main__":
    main()