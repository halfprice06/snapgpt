#!/usr/bin/env python3

import os
from pathlib import Path
import argparse
import subprocess
import shutil
import sys
import json
from typing import List, Set, Tuple
from termcolor import colored, cprint  # for colored output
import pyperclip  # for clipboard support

CONFIG_DIR = Path.home() / '.config' / 'snapgpt'
CONFIG_FILE = CONFIG_DIR / 'config.json'

# Default configuration
DEFAULT_CONFIG = {
    'default_editor': 'cursor',
    'auto_copy_to_clipboard': True,  # New setting for clipboard behavior
    'first_time_setup_done': False,  # Track if first-time setup is completed
    'file_extensions': [
        # Core code files
        ".py", ".js", ".ts", ".jsx", ".tsx",  # Python, JavaScript, TypeScript
        ".go", ".rs", ".java",                # Go, Rust, Java
        ".cpp", ".c", ".h",                   # C/C++
        # Configuration
        ".toml", ".yaml", ".yml", ".json",    # Config files
        # Documentation
        ".md"                                 # Documentation
    ],
    'exclude_dirs': [
        # Build artifacts
        "__pycache__", "build", "dist", "*.egg-info",
        # Dependencies
        "venv", ".venv", "env", "node_modules", "vendor", "third_party",
        # Version control
        ".git", ".svn", ".hg",
        # IDE/Editor
        ".idea", ".vscode", ".vs",
        # Test coverage/cache
        ".pytest_cache", ".coverage", "htmlcov",
        # Temporary/cache
        "tmp", "temp", ".cache",
        # Logs
        "logs", "log"
    ]
}

def get_config():
    """Get configuration from config file, using defaults for missing values."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                config = json.load(f)
                # Merge with defaults, keeping user values where they exist
                return {**DEFAULT_CONFIG, **config}
        except (json.JSONDecodeError, IOError):
            return DEFAULT_CONFIG
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

def get_default_editor():
    """Get the default editor from config file."""
    return get_config()['default_editor']

def get_default_extensions():
    """Get the default file extensions from config file."""
    return get_config()['file_extensions']

def get_default_exclude_dirs():
    """Get the default excluded directories from config file."""
    return get_config()['exclude_dirs']

def set_default_editor(editor: str, quiet: bool = False) -> bool:
    """Set the default editor in config file."""
    editor = editor.lower()
    valid_editors = {'cursor', 'code', 'windsurf', 'zed', 'xcode'}
    
    if editor not in valid_editors:
        print_error(f"Invalid editor: {editor}. Valid options are: {', '.join(valid_editors)}", quiet)
        return False
    
    config = get_config()
    config['default_editor'] = editor
    if save_config(config):
        print_progress(f"Default editor set to: {editor}", quiet)
        return True
    return False

def set_default_extensions(extensions: List[str], quiet: bool = False) -> bool:
    """Set the default file extensions in config file."""
    # Ensure all extensions start with a dot
    extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in extensions]
    
    config = get_config()
    config['file_extensions'] = extensions
    if save_config(config):
        print_progress(f"Default file extensions updated", quiet)
        return True
    return False

def set_default_exclude_dirs(dirs: List[str], quiet: bool = False) -> bool:
    """Set the default excluded directories in config file."""
    config = get_config()
    config['exclude_dirs'] = dirs
    if save_config(config):
        print_progress(f"Default excluded directories updated", quiet)
        return True
    return False

def print_warning(msg: str, quiet: bool = False):
    """Print a warning message in yellow unless quiet mode is enabled."""
    if not quiet:
        cprint(f"\nWarning: {msg}", 'yellow')

def print_error(msg: str, quiet: bool = False):
    """Print an error message in red unless quiet mode is enabled."""
    if not quiet:
        cprint(f"\nError: {msg}", 'red')

def print_progress(msg: str, quiet: bool = False, end="\n"):
    """Print a progress message in green unless quiet mode is enabled."""
    if not quiet:
        cprint(msg, 'green', end=end)

def create_directory_tree(
    directories: List[str],
    exclude_dirs: Set[str],
    include_file_extensions: Set[str],
    max_file_size: int,
    max_depth: int,
    quiet: bool
) -> Tuple[str, List[Path]]:
    """
    Creates an ASCII representation of the directory structure, including files.
    """
    tree_output = ["# Directory Structure", ""]
    file_order = []  # Keep track of files in order
    skipped_paths = []  # Track skipped paths
    permission_errors = []  # Track permission errors
    large_files = []  # Track files exceeding size limit
    
    # Define proper Unicode box-drawing characters
    BOX_VERTICAL = "│"
    BOX_HORIZONTAL = "─"
    BOX_VERTICAL_RIGHT = "├"
    BOX_UP_RIGHT = "└"
    BOX_SPACE = " "
    
    def add_to_tree(path, prefix="", is_last=False, current_depth=0):
        # Check depth limit
        if max_depth > 0 and current_depth > max_depth:
            return
        
        # Get the relative name for display
        display_name = path.name or str(path)
        
        # Add current item to the tree using proper box-drawing characters
        tree_output.append(f"{prefix}{BOX_UP_RIGHT if is_last else BOX_VERTICAL_RIGHT}{BOX_HORIZONTAL*2} {display_name}")
        
        # If it's a file, add it to file_order and return
        if path.is_file():
            file_size = path.stat().st_size
            is_valid_extension = path.suffix.lower() in include_file_extensions
            
            if is_valid_extension:
                if max_file_size > 0 and file_size > max_file_size:
                    large_files.append((str(path), file_size / 1_000_000))
                else:
                    file_order.append(path)
            return
        
        # For directories, process contents
        try:
            items = sorted(path.iterdir())
            # Filter out excluded directories and hidden files
            items = [item for item in items 
                    if not (item.name in exclude_dirs or item.name.startswith('.'))]
        except PermissionError:
            permission_errors.append(str(path))
            return
        except NotADirectoryError:
            return
        
        # Separate directories and files
        dirs = [item for item in items if item.is_dir() and item.name not in exclude_dirs]
        files = [item for item in items if item.is_file()]
        
        # Combine and get total count for determining 'is_last'
        all_items = dirs + files
        items_count = len(all_items)
        
        # Process all items
        for index, item in enumerate(all_items):
            new_prefix = prefix + (BOX_SPACE * 4 if is_last else f"{BOX_VERTICAL}{BOX_SPACE*3}")
            is_last_item = index == items_count - 1
            add_to_tree(item, new_prefix, is_last_item, current_depth + 1)
    
    # Process each input path
    for directory in directories:
        path = Path(directory).resolve()
        if not path.exists():
            skipped_paths.append(str(path))
            continue
            
        # If it's a file, create a parent directory node
        if path.is_file():
            parent_display = path.parent.name or str(path.parent)
            tree_output.append(f"{BOX_UP_RIGHT}{BOX_HORIZONTAL*2} {parent_display}")
            tree_output.append(f"    {BOX_UP_RIGHT}{BOX_HORIZONTAL*2} {path.name}")
            
            file_size = path.stat().st_size
            is_valid_extension = path.suffix.lower() in include_file_extensions
            
            if is_valid_extension:
                if max_file_size > 0 and file_size > max_file_size:
                    large_files.append((str(path), file_size / 1_000_000))
                else:
                    file_order.append(path)
        else:
            add_to_tree(path, "", True)
        tree_output.append("")  # Add blank line between directories
    
    # Print warnings
    if skipped_paths:
        print_warning("The following paths do not exist:", quiet)
        for path in skipped_paths:
            print(f"  - {path}")
    
    if permission_errors:
        print_warning("Permission denied for the following directories:", quiet)
        for path in permission_errors:
            print(f"  - {path}")
    
    if large_files:
        print_warning(f"The following files exceed the size limit ({max_file_size / 1_000_000:.1f}MB):", quiet)
        for path, size in large_files:
            print(f"  - {path} ({size:.1f}MB)")
    
    if not file_order:
        print_warning(f"No files found matching the specified extensions: {', '.join(include_file_extensions)}", quiet)
    
    return "\n".join(tree_output), file_order

def do_first_time_setup(quiet: bool = False) -> None:
    """
    Perform first-time setup by asking the user for their preferences.
    """
    config = get_config()
    
    if not config.get('first_time_setup_done', False):
        print("\nWelcome to snapgpt! Let's set up your preferences.\n")
        
        # Ask for default editor
        editors = ['cursor', 'code', 'windsurf', 'zed', 'xcode']
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
        
        # Ask for clipboard preference
        while True:
            choice = input("\nWould you like snapshots to be automatically copied to clipboard? (y/n): ").lower()
            if choice in ('y', 'n'):
                config['auto_copy_to_clipboard'] = (choice == 'y')
                break
            print("Please enter 'y' for yes or 'n' for no.")
        
        # Mark setup as complete
        config['first_time_setup_done'] = True
        save_config(config)
        print("\nSetup complete! You can change these settings later using command line options.\n")

def is_system_directory(path: str) -> bool:
    """
    Check if the given path is a system directory that should trigger a warning.
    Only warns for direct system directories, not their subdirectories.
    """
    system_dirs = {
        # Windows system directories
        r"C:\Windows", r"C:\Program Files", r"C:\Program Files (x86)",
        # macOS system directories
        "/System", "/Library", "/Applications", "/usr", "/bin", "/sbin",
        # Linux system directories
        "/etc", "/var", "/opt", "/root", "/usr", "/bin", "/sbin", "/lib", "/dev"
    }
    
    # Convert path to absolute and normalize
    abs_path = os.path.abspath(path)
    
    # Check if the path exactly matches a system directory
    for sys_dir in system_dirs:
        try:
            # Normalize both paths for comparison
            norm_sys_dir = os.path.normpath(sys_dir)
            norm_path = os.path.normpath(abs_path)
            if norm_path == norm_sys_dir:
                return True
        except ValueError:
            continue
    return False

def is_git_repository(path: str) -> bool:
    """
    Check if the given path is inside a Git repository.
    """
    try:
        # Start from the given path and traverse up until we find .git
        current = os.path.abspath(path)
        while current != os.path.dirname(current):  # Stop at root
            if os.path.exists(os.path.join(current, '.git')):
                return True
            current = os.path.dirname(current)
        return False
    except Exception:
        return False

def create_code_snapshot(
    directories=["."],
    files=None,
    output_file="full_code_snapshot.txt",
    include_file_extensions=(
        # Core code files
        ".py", ".js", ".ts", ".jsx", ".tsx",  # Python, JavaScript, TypeScript
        ".go", ".rs", ".java",                # Go, Rust, Java
        ".cpp", ".c", ".h",                   # C/C++
        # Configuration
        ".toml", ".yaml", ".yml", ".json",    # Config files
        # Documentation
        ".md"                                 # Documentation
    ),
    exclude_dirs={
        # Build artifacts
        "__pycache__", "build", "dist", "*.egg-info",
        # Dependencies
        "venv", ".venv", "env", "node_modules", "vendor", "third_party",
        # Version control
        ".git", ".svn", ".hg",
        # IDE/Editor
        ".idea", ".vscode", ".vs",
        # Test coverage/cache
        ".pytest_cache", ".coverage", "htmlcov",
        # Temporary/cache
        "tmp", "temp", ".cache",
        # Logs
        "logs", "log"
    },
    max_file_size=0,
    max_depth=0,
    quiet=False
):
    """
    Recursively collects all code files from the specified directories and concatenates them into a single file.
    Focuses on files that are most relevant for code review and LLM context.
    Also copies the content to clipboard if enabled in config.
    """
    print_progress(f"Processing directories: {', '.join(directories)}", quiet)
    
    # Check directories for warnings
    for directory in directories:
        abs_dir = os.path.abspath(directory)
        
        # Check for system directories
        if is_system_directory(abs_dir):
            print_warning(f"Warning: '{directory}' appears to be a system directory or subdirectory. Scanning system directories is not recommended.", quiet)
            user_input = input("Do you want to continue? (y/n): ").lower() if not quiet else 'n'
            if user_input != 'y':
                print_progress("Operation cancelled by user.", quiet)
                sys.exit(0)
        
        # Check if not in a Git repository
        if not is_git_repository(abs_dir):
            print_warning(f"Warning: '{directory}' is not part of a Git repository. This might not be a code project directory.", quiet)
            user_input = input("Do you want to continue? (y/n): ").lower() if not quiet else 'n'
            if user_input != 'y':
                print_progress("Operation cancelled by user.", quiet)
                sys.exit(0)
    
    # Get clipboard preference from config
    config = get_config()
    auto_copy = config.get('auto_copy_to_clipboard', True)
    
    # Resolve directories relative to current working directory
    resolved_dirs = [Path(d).resolve() for d in directories]

    # If specific files are provided, use those instead of scanning directories
    if files:
        resolved_files = [Path(f).resolve() for f in files]
        file_order = []
        for file in resolved_files:
            if not file.exists():
                print_warning(f"File not found: {file}", quiet)
                continue
            if file.suffix.lower() in include_file_extensions:
                file_order.append(file)
            else:
                print_warning(f"Skipping file with unsupported extension: {file}", quiet)
        
        # Create a simplified tree for specific files
        tree_output = ["# Selected Files", ""]
        for file in file_order:
            tree_output.append(f"└── {file.name}")
        directory_tree = "\n".join(tree_output)
    else:
        # Use the existing directory tree creation for directories
        directory_tree, file_order = create_directory_tree(
            resolved_dirs, exclude_dirs, include_file_extensions,
            max_file_size, max_depth, quiet
        )

    # Prepare output file
    output_path = Path(output_file).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Use a string buffer to collect all content
    content_buffer = []
    
    with open(output_path, "w", encoding="utf-8") as out_f:
        # First, add the directory tree and get the file order
        out_f.write(directory_tree)
        content_buffer.append(directory_tree)
        
        out_f.write("\n\n# ======= File Contents =======\n\n")
        content_buffer.append("\n\n# ======= File Contents =======\n\n")
        
        # Process files in the same order as they appear in the tree
        total_files = len(file_order)
        for idx, file_path in enumerate(file_order, 1):
            # Show progress
            if not quiet:
                print(f"\rProcessing files: {colored(str(idx), 'cyan')}/{colored(str(total_files), 'cyan')}", end="", flush=True)
            
            # Write a header to indicate the start of this file's content
            try:
                relative_path = file_path.relative_to(next(d for d in resolved_dirs if str(file_path).startswith(str(d))).parent)
                header = f"\n\n# ======= File: {relative_path} =======\n\n"
                out_f.write(header)
                content_buffer.append(header)
                
                # Read and append file content
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    out_f.write(content)
                    content_buffer.append(content)
                except Exception as e:
                    print_error(f"Error reading {file_path}: {e}", quiet)
                    continue
            except (StopIteration, ValueError):
                print_warning(f"Could not determine relative path for {file_path}", quiet)
                continue
        
        if not quiet:
            print()  # New line after progress
    
    # Copy content to clipboard if enabled
    if auto_copy:
        try:
            pyperclip.copy(''.join(content_buffer))
            print_progress("Content copied to clipboard", quiet)
        except Exception as e:
            print_warning(f"Could not copy to clipboard: {e}", quiet)
    
    print_progress(f"\nCode snapshot created at: {output_path}", quiet)
    return str(output_path)

def find_editor_on_windows(editor: str) -> str:
    """
    Find the editor executable on Windows by checking common installation locations.
    Returns the path to the executable if found, None otherwise.
    """
    editor_paths = {
        'cursor': [
            r"%LOCALAPPDATA%\Programs\Cursor\Cursor.exe",
            r"%LOCALAPPDATA%\Cursor\Cursor.exe",
            r"%PROGRAMFILES%\Cursor\Cursor.exe",
            r"%PROGRAMFILES(X86)%\Cursor\Cursor.exe",
        ],
        'code': [
            r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe",
            r"%PROGRAMFILES%\Microsoft VS Code\Code.exe",
            r"%PROGRAMFILES(X86)%\Microsoft VS Code\Code.exe",
        ],
        'windsurf': [
            r"%LOCALAPPDATA%\Programs\Windsurf\Windsurf.exe",
            r"%PROGRAMFILES%\Windsurf\Windsurf.exe",
        ],
        'zed': [
            r"%LOCALAPPDATA%\Programs\Zed\Zed.exe",
            r"%PROGRAMFILES%\Zed\Zed.exe",
        ]
    }

    if editor not in editor_paths:
        return None

    for path in editor_paths[editor]:
        expanded_path = os.path.expandvars(path)
        if os.path.isfile(expanded_path):
            return expanded_path
    return None

def try_open_in_editor_windows(editor: str, file_path: str, quiet: bool = False) -> bool:
    """
    Try to open a file in the specified editor on Windows.
    Returns True if successful, False otherwise.
    """
    editor_path = find_editor_on_windows(editor)
    if editor_path and editor_path.lower().endswith(f'{editor}.exe'):
        try:
            # Get the current directory and absolute file path
            current_dir = os.path.dirname(os.path.abspath(file_path))
            abs_file_path = os.path.abspath(file_path)

            # First open the folder, then the file
            with open(os.devnull, 'w') as devnull:
                subprocess.Popen([editor_path, current_dir], stderr=devnull)
                subprocess.Popen([editor_path, abs_file_path], stderr=devnull)
            print_progress(f"Opened {file_path} in {editor.title()}", quiet)
            return True

        except (subprocess.SubprocessError, OSError):
            # Try CLI script for editors that have one (like Cursor)
            if editor == 'cursor':
                cli_path = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Cursor\resources\app\out\cli.js")
                if os.path.isfile(cli_path):
                    try:
                        with open(os.devnull, 'w') as devnull:
                            subprocess.Popen(['node', cli_path, current_dir], stderr=devnull)
                            subprocess.Popen(['node', cli_path, abs_file_path], stderr=devnull)
                        print_progress(f"Opened {file_path} in {editor.title()} using CLI", quiet)
                        return True
                    except (subprocess.SubprocessError, OSError):
                        pass

    # If all methods fail, return False
    if not quiet:
        print_warning(f"Could not open {editor.title()}. Please make sure it is installed correctly.")
    return False

def find_editor_path(editor: str) -> str:
    """
    Find the editor executable by checking common installation locations.
    Returns the path to the executable if found, None otherwise.
    """
    if sys.platform == 'win32':
        return find_editor_on_windows(editor)

    # Common paths for Mac and Linux
    editor_paths = {
        'cursor': [
            # Mac paths
            '/Applications/Cursor.app/Contents/MacOS/Cursor',
            # Linux paths
            '/usr/bin/cursor',
            '/usr/local/bin/cursor',
            '~/.local/bin/cursor'
        ],
        'code': [
            # Mac paths
            '/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code',
            # Linux paths
            '/usr/bin/code',
            '/usr/local/bin/code',
            '~/.local/bin/code'
        ],
        'windsurf': [
            # Mac paths
            '/Applications/Windsurf.app/Contents/MacOS/Windsurf',
            # Linux paths
            '/usr/bin/windsurf',
            '/usr/local/bin/windsurf',
            '~/.local/bin/windsurf'
        ],
        'zed': [
            # Mac paths
            '/Applications/Zed.app/Contents/MacOS/Zed',
            # Linux paths
            '/usr/bin/zed',
            '/usr/local/bin/zed',
            '~/.local/bin/zed'
        ]
    }

    if editor not in editor_paths:
        return None

    # First, check if the command is in PATH
    path_cmd = shutil.which(editor)
    if path_cmd:
        return path_cmd

    # Then check common installation locations
    for path in editor_paths[editor]:
        expanded_path = os.path.expanduser(path)
        if os.path.isfile(expanded_path):
            return expanded_path

    return None

def open_in_editor(file_path, editor='cursor', quiet=False):
    """
    Attempts to open the file in the specified editor.
    Handles platform-specific paths and commands.
    """
    editor = editor.lower()
    editor_commands = {
        'cursor': 'cursor',
        'code': 'code',
        'windsurf': 'windsurf',
        'zed': 'zed',
        'xcode': 'xed'  # xed is the command line tool for Xcode
    }

    # Special handling for Xcode on non-macOS systems
    if editor == 'xcode' and sys.platform != 'darwin':
        print_error("Xcode is only available on macOS", quiet)
        return

    # Handle Windows-specific cases
    if sys.platform == 'win32' and editor in ['cursor', 'code', 'windsurf', 'zed']:
        if try_open_in_editor_windows(editor, file_path, quiet):
            return

    # For non-Windows systems
    editor_cmd = editor_commands.get(editor)
    if not editor_cmd:
        print_error(f"Unsupported editor: {editor}. Supported editors are: {', '.join(editor_commands.keys())}", quiet)
        return

    # Try to find the editor executable
    editor_path = find_editor_path(editor)
    if editor_path:
        try:
            # Get absolute paths
            current_dir = os.path.dirname(os.path.abspath(file_path))
            abs_file_path = os.path.abspath(file_path)
            
            # Special handling for macOS .app bundles
            if sys.platform == 'darwin' and editor != 'xcode':
                # If it's an .app bundle executable, use the 'open' command
                if '.app/Contents/MacOS' in editor_path:
                    with open(os.devnull, 'w') as devnull:
                        subprocess.Popen(['open', '-a', editor_path.split('/Contents/MacOS/')[0], current_dir], stderr=devnull)
                        subprocess.Popen(['open', '-a', editor_path.split('/Contents/MacOS/')[0], abs_file_path], stderr=devnull)
                else:
                    with open(os.devnull, 'w') as devnull:
                        subprocess.Popen([editor_path, current_dir], stderr=devnull)
                        subprocess.Popen([editor_path, abs_file_path], stderr=devnull)
            else:
                # Linux or non-app macOS executables
                with open(os.devnull, 'w') as devnull:
                    subprocess.Popen([editor_path, current_dir], stderr=devnull)
                    subprocess.Popen([editor_path, abs_file_path], stderr=devnull)
            
            print_progress(f"Opened {file_path} in {editor.title()}", quiet)
            return
        except (subprocess.SubprocessError, OSError):
            pass

    # If everything fails, try system default
    try:
        if sys.platform == 'darwin':  # macOS
            subprocess.run(['open', file_path], check=True)
        elif sys.platform == 'win32':  # Windows
            os.startfile(file_path)
        else:  # Linux and others
            subprocess.run(['xdg-open', file_path], check=True)
        print_progress(f"Opened {file_path} in system default editor", quiet)
    except (subprocess.SubprocessError, FileNotFoundError, AttributeError):
        print_error(f"Failed to open file in any editor", quiet)
        return

def main():
    # Do first-time setup if needed
    do_first_time_setup()
    
    parser = argparse.ArgumentParser(
        description='Create a snapshot of code files in specified directories, optimized for LLM context.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-d', '--directories', nargs='+', default=["."],
                      help='List of directories to scan')
    parser.add_argument('-f', '--files', nargs='+',
                      help='List of specific files to include (overrides directory scanning)')
    parser.add_argument('-o', '--output', default="full_code_snapshot.txt",
                      help='Output file path')
    parser.add_argument('-e', '--extensions', nargs='+',
                      default=None,  # Will use config value if None
                      help='File extensions to include (e.g., .py .js .md)')
    parser.add_argument('--exclude-dirs', nargs='+',
                      default=None,  # Will use config value if None
                      help='Directories to exclude from scanning')
    parser.add_argument('--no-open', action='store_true',
                      help='Do not automatically open the snapshot in an editor')
    parser.add_argument('--editor', choices=['cursor', 'code', 'windsurf', 'zed', 'xcode'], default=None,
                      help='Editor to open the snapshot in (default: from config)')
    parser.add_argument('--set-default-editor', choices=['cursor', 'code', 'windsurf', 'zed', 'xcode'],
                      help='Set the default editor and exit')
    parser.add_argument('--set-default-extensions', nargs='+',
                      help='Set the default file extensions and exit')
    parser.add_argument('--set-default-exclude-dirs', nargs='+',
                      help='Set the default excluded directories and exit')
    parser.add_argument('--max-size', type=float, default=0,
                      help='Maximum file size in MB (0 for no limit)')
    parser.add_argument('--max-depth', type=int, default=0,
                      help='Maximum directory depth (0 for no limit)')
    parser.add_argument('-q', '--quiet', action='store_true',
                      help='Suppress progress output and non-error messages')
    parser.add_argument('--no-copy', action='store_true',
                      help='Do not copy the snapshot to clipboard')

    args = parser.parse_args()
    
    # Handle setting defaults
    if args.set_default_editor:
        success = set_default_editor(args.set_default_editor, args.quiet)
        sys.exit(0 if success else 1)
    
    if args.set_default_extensions:
        success = set_default_extensions(args.set_default_extensions, args.quiet)
        sys.exit(0 if success else 1)
    
    if args.set_default_exclude_dirs:
        success = set_default_exclude_dirs(args.set_default_exclude_dirs, args.quiet)
        sys.exit(0 if success else 1)
    
    # Temporarily override auto_copy setting if --no-copy is used
    if args.no_copy:
        config = get_config()
        config['auto_copy_to_clipboard'] = False
        save_config(config)
    
    # Use values from args or config
    editor = args.editor or get_default_editor()
    extensions = args.extensions or get_default_extensions()
    exclude_dirs = args.exclude_dirs or get_default_exclude_dirs()
    
    output_path = create_code_snapshot(
        directories=args.directories,
        files=args.files,  # Pass the files argument
        output_file=args.output,
        include_file_extensions=tuple(ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in extensions),
        exclude_dirs=set(exclude_dirs),
        max_file_size=int(args.max_size * 1_000_000) if args.max_size > 0 else 0,
        max_depth=args.max_depth,
        quiet=args.quiet
    )

    if not args.no_open:
        open_in_editor(output_path, editor, args.quiet)

if __name__ == "__main__":
    main()