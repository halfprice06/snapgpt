# ======= File: setup.py =======
import os
import platform
import subprocess
import shutil
from setuptools import setup, find_packages
from setuptools.command.install import install


class IntegrationInstall(install):
    """
    Custom install class that attempts to set up macOS and Windows
    context menu integration after SnapGPT is installed.
    """
    def run(self):
        # Run normal install steps first
        super().run()

        # Where is SnapGPT installed?
        snapgpt_path = shutil.which("snapgpt") or "snapgpt"

        # Attempt macOS integration
        if platform.system() == "Darwin":
            self.setup_macos_quick_action(snapgpt_path)
        
        # Attempt Windows integration
        elif platform.system() == "Windows":
            self.setup_windows_registry(snapgpt_path)

    def setup_macos_quick_action(self, snapgpt_path):
        """
        Copy the SnapGPT.workflow file to ~/Library/Services/.
        This gives a right-click "Services" -> "SnapGPT" option in Finder.
        """
        print("[IntegrationInstall] Setting up macOS Finder Quick Action...")

        # path to the .workflow file inside this package
        pkg_root = os.path.dirname(os.path.abspath(__file__))
        workflow_src = os.path.join(pkg_root, "snapgpt", "resources", "SnapGPT.workflow")
        if not os.path.isdir(workflow_src):
            print(f" [WARN] Could not find {workflow_src}. Skipping macOS integration.")
            return

        # Destination: ~/Library/Services/SnapGPT.workflow
        workflow_dest = os.path.expanduser("~/Library/Services/SnapGPT.workflow")
        try:
            os.makedirs(os.path.dirname(workflow_dest), exist_ok=True)
            # Remove any old copy
            if os.path.exists(workflow_dest):
                shutil.rmtree(workflow_dest)
            # Copy the entire .workflow folder
            shutil.copytree(workflow_src, workflow_dest)
            print(f" [OK] Copied SnapGPT.workflow to {workflow_dest}")
            print(" [NOTE] Right-click a file/folder in Finder, select 'Services', then 'SnapGPT'!")
        except Exception as e:
            print(f" [ERROR] Could not install macOS Quick Action: {e}")

    def setup_windows_registry(self, snapgpt_path):
        """
        Import snapgpt_context.reg to HKEY_CURRENT_USER.
        Also place snapgpt_context.bat in the same Scripts folder as snapgpt.exe, if possible.
        """
        print("[IntegrationInstall] Setting up Windows Explorer context menu...")

        pkg_root = os.path.dirname(os.path.abspath(__file__))
        bat_src = os.path.join(pkg_root, "snapgpt", "resources", "snapgpt_context.bat")
        reg_src = os.path.join(pkg_root, "snapgpt", "resources", "snapgpt_context.reg")

        if not os.path.isfile(bat_src) or not os.path.isfile(reg_src):
            print(f" [WARN] Missing bat/reg files. Skipping Windows integration.")
            return

        # Where is snapgpt.exe or python scripts folder?
        # Typically something like C:\Users\You\AppData\Local\Programs\Python\PythonXY\Scripts
        scripts_dir = os.path.dirname(snapgpt_path) if snapgpt_path else ""
        if scripts_dir and os.path.isdir(scripts_dir):
            # Copy snapgpt_context.bat so the .reg file can reference it easily
            bat_dest = os.path.join(scripts_dir, "snapgpt_context.bat")
            try:
                shutil.copyfile(bat_src, bat_dest)
                print(f" [OK] Copied snapgpt_context.bat to {bat_dest}")
            except Exception as e:
                print(f" [ERROR] Could not copy .bat file: {e}")
        else:
            print(" [WARN] Could not find a suitable Scripts dir. The .reg file may not work correctly.")

        # Now we import the .reg under HKEY_CURRENT_USER
        # That avoids needing admin privileges in most cases.
        try:
            print(" [INFO] Importing snapgpt_context.reg into HKEY_CURRENT_USER...")
            subprocess.run(["reg", "import", reg_src], check=True, shell=True)
            print(" [OK] Registry import successful. Right-click integration should now appear.")
        except Exception as e:
            print(f" [ERROR] Registry import failed: {e}")


# Read the README for the long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="snapgpt",
    version="0.2.1",
    author="Daniel Price",
    author_email="",
    description="A tool to create readable snapshots of your codebase",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/halfprice06/snapgpt",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    entry_points={
        'console_scripts': [
            'snapgpt=snapgpt.cli.main:main',
        ],
    },
    python_requires=">=3.7",
    cmdclass={
        'install': IntegrationInstall
    }
)