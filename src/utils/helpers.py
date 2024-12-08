import os
import platform
import subprocess
from colorama import Fore, Style

def clear_screen():
    try:
        if platform.system() == "Windows":
            subprocess.run("cls", shell=True)
        else:
            subprocess.run("clear", shell=True)
    except:
        print("\n" * 100)

def ensure_directory(path):
    os.makedirs(path, exist_ok=True)

def delete_file(file_path):
    try:
        # Convert bytes to string if needed
        if isinstance(file_path, bytes):
            file_path = file_path.decode()
            
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"{Fore.GREEN}File deleted: {file_path}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}File not found: {file_path}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error deleting file: {str(e)}{Style.RESET_ALL}")

def extract_username(email: str) -> str:
    """Extract username part from email address."""
    try:
        return email.split('@')[0]
    except:
        return email

def validate_email(email):
    return '@' in email and '.' in email.split('@')[1]