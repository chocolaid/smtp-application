import sys
import os
from cx_Freeze import setup, Executable
import src.config.version as version

sys.setrecursionlimit(15000)

build_exe_options = {
    "includes": [
        "colorama", 
        "cryptography", 
        "pandas", 
        "packaging",
        "git",  # Add GitPython dependency
        "smtplib",
        "ssl",
        "email"
    ],
    "packages": [
        "os",
        "sys",
        "json",
        "logging",
        "datetime",
        "tempfile",
        "shutil",
        "platform",
        "subprocess",
        "smtplib",
        "ssl",
        "email",
        "getpass",
        "typing",
        "src"  # Include the entire src package
    ],
    "excludes": ["tkinter", "test", "distutils", "unittest"],
    "include_files": [
        (os.path.abspath("data"), "data"),
        (os.path.abspath("assets"), "assets"),
        (os.path.abspath("version.json"), "version.json")
    ],
    "build_exe": "build/SMTP_Manager",
    "include_msvcr": True,
}

base = None

setup(
    name="SMTP Manager",
    version=version.VERSION,
    description="SMTP Manager",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base)],
)