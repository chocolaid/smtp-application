import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
# "packages": ["os"] is used as example only
build_exe_options = {
    "packages": [
        "os",
        "sys",
        "json",
        "logging",
        "colorama",
        "cryptography",
        "datetime",
        "tempfile",
        "shutil",
        "platform",
        "subprocess",
        "git",
        "packaging",
        "smtplib",
        "ssl",
        "email",
        "getpass",
        "typing",
        "cx_Freeze"
    ],
    "excludes": [
        "tkinter",
        "test",
        "distutils"
    ],
    "include_files": [
        ("data", "data"),
        ("assets", "assets")
    ],
    "build_exe": "build/SMTP Manager",
    "zip_include_packages": "*",
    "zip_exclude_packages": None,
    "include_msvcr": True,
    
}
# base="Win32GUI" should be used only for Windows GUI app
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name = "SMTP Manager",
    version = "2.0.0",
    description = "SMTP Manager",
    options = {"build_exe": build_exe_options},
    executables = [Executable("main.py", base=base)]
)