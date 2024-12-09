import sys
import os
from cx_Freeze import setup, Executable

sys.setrecursionlimit(15000)

build_exe_options = {
    "includes": ["colorama", "cryptography", "pandas", "packaging"],
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
        "typing"
    ],
    "excludes": ["tkinter", "test", "distutils", "unittest"],
    "include_files": [
        (os.path.abspath("data"), "data"),
        (os.path.abspath("assets"), "assets")
    ],
    "build_exe": "build/SMTP_Manager",
    "include_msvcr": True,
}

base = None

setup(
    name="SMTP Manager",
    version="2.0.0",
    description="SMTP Manager",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base)],
)
