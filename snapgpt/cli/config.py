import json
import sys
import os
from pathlib import Path
from termcolor import cprint
from typing import List

CONFIG_DIR = Path.home() / '.config' / 'snapgpt'
CONFIG_FILE = CONFIG_DIR / 'config.json'

DEFAULT_CONFIG = {
    'file_extensions': [
        # Code files
        ".py", ".js", ".ts", ".jsx", ".tsx",
        ".go", ".rs", ".java",
        ".cpp", ".c", ".h", ".html",
        
        # Config files
        ".toml", ".yaml", ".yml", ".json",
        
        # Documentation files
        ".md", 
        
        # Office documents
        ".doc", ".docx",
        ".pdf",
        ".xls", ".xlsx",
        ".ppt", ".pptx",
        
        # Media files
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"
    ],
    'exclude_dirs': [
        "__pycache__", "build", "dist", "*.egg-info",
        "venv", ".venv", "env", "node_modules", "vendor",
        ".git", ".svn", ".hg",
        ".idea", ".vscode", ".vs",
        ".pytest_cache", ".coverage", "htmlcov",
        "tmp", "temp", ".cache",
        "logs", "log"
    ]
}

def cprint_colored(message, color='green', end="\n"):
    cprint(message, color, end=end)

def print_warning(msg: str, quiet: bool = False):
    if not quiet:
        cprint(f"\nWarning: {msg}", 'yellow')

def print_error(msg: str, quiet: bool = False):
    if not quiet:
        cprint(f"\nError: {msg}", 'red')

def print_progress(msg: str, quiet: bool = False, end="\n"):
    if not quiet:
        cprint_colored(msg, 'green', end=end)


def get_config():
    """Get configuration from config file, using defaults for missing values."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                config = json.load(f)
            
            # Merge file extensions instead of overwriting
            if 'file_extensions' in config:
                config['file_extensions'] = list(set(DEFAULT_CONFIG['file_extensions'] + config['file_extensions']))
            
            final_config = {**DEFAULT_CONFIG, **config}
            return final_config
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULT_CONFIG


def save_config(config):
    """Save configuration to config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except IOError as e:
        print_error(f"Failed to save config: {e}")
        return False


def do_first_time_setup(quiet: bool = False) -> None:
    config = get_config()
    if not config.get('first_time_setup_done', False):
        print("\nWelcome to snapgpt! Let's set up your preferences.\n")
        editors = ['cursor', 'code', 'windsurf', 'zed', 'xcode', 'textedit']
        print("Available editors:")
        for i, editor in enumerate(editors, 1):
            print(f"{i}. {editor.title()}")

        while True:
            try:
                choice = input("\nWhich editor would you like to use as default? (enter number): ")
                editor_index = int(choice) - 1
                if 0 <= editor_index < len(editors):
                    config['default_editor'] = editors[editor_index]
                    break
                print("Invalid choice. Please enter a number from the list.")
            except ValueError:
                print("Please enter a valid number.")

        while True:
            choice = input("\nWould you like snapshots to be automatically copied to clipboard? (y/n): ").lower()
            if choice in ('y', 'n'):
                config['auto_copy_to_clipboard'] = (choice == 'y')
                break
            print("Please enter 'y' for yes or 'n' for no.")

        config['first_time_setup_done'] = True
        save_config(config)
        print("\nSetup complete! You can change these settings later using command line options.\n")


def set_default_editor(editor: str, quiet: bool = False) -> bool:
    editor = editor.lower()
    # Now includes 'textedit'
    valid_editors = {'cursor', 'code', 'windsurf', 'zed', 'xcode', 'textedit'}

    if editor not in valid_editors:
        print_error(f"Invalid editor: {editor}. Valid: {', '.join(valid_editors)}", quiet)
        return False

    config = get_config()
    config['default_editor'] = editor
    if save_config(config):
        print_progress(f"Default editor set to: {editor}", quiet)
        return True
    return False


def set_default_extensions(extensions: List[str], quiet: bool = False) -> bool:
    extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in extensions]
    config = get_config()
    config['file_extensions'] = extensions
    if save_config(config):
        print_progress("Default file extensions updated", quiet)
        return True
    return False


def set_default_exclude_dirs(dirs: List[str], quiet: bool = False) -> bool:
    config = get_config()
    config['exclude_dirs'] = dirs
    if save_config(config):
        print_progress("Default excluded directories updated", quiet)
        return True
    return False


def get_default_editor():
    return get_config().get('default_editor', 'cursor')


def get_default_extensions():
    return get_config()['file_extensions']


def get_default_exclude_dirs():
    return get_config()['exclude_dirs']


def is_system_directory(path: str) -> bool:
    system_dirs = {
        r"C:\Windows", r"C:\Program Files", r"C:\Program Files (x86)",
        "/System", "/Library", "/Applications", "/usr", "/bin", "/sbin",
        "/etc", "/var", "/opt", "/root", "/lib", "/dev"
    }
    abs_path = os.path.abspath(path)
    for sys_dir in system_dirs:
        try:
            norm_sys_dir = os.path.normpath(sys_dir)
            norm_path = os.path.normpath(abs_path)
            if norm_path == norm_sys_dir:
                return True
        except ValueError:
            continue
    return False


def is_git_repository(path: str) -> bool:
    try:
        import os
        current = os.path.abspath(path)
        while current != os.path.dirname(current):
            if os.path.exists(os.path.join(current, '.git')):
                return True
            current = os.path.dirname(current)
        return False
    except Exception:
        return False