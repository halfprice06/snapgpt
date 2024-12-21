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

CONFIG_DIR = Path.home() / '.config' / 'snapgpt'
CONFIG_FILE = CONFIG_DIR / 'config.json'

# Default configuration
DEFAULT_CONFIG = {
    'default_editor': 'cursor',
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
    valid_editors = {'cursor', 'code', 'windsurfer'}
    
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
    
    def add_to_tree(path, prefix="", is_last=False, current_depth=0):
        # Check depth limit
        if max_depth > 0 and current_depth > max_depth:
            return
        
        # Get the relative name for display
        display_name = path.name or str(path)
        
        # Add current item to the tree
        tree_output.append(f"{prefix}{'└── ' if is_last else '├── '}{display_name}")
        
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
            new_prefix = prefix + ("    " if is_last else "│   ")
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
            tree_output.append(f"└── {parent_display}")
            tree_output.append(f"    └── {path.name}")
            
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

def create_code_snapshot(
    directories=["."],
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
    max_file_size=0,  # 0 means no limit
    max_depth=0,      # 0 means no limit
    quiet=False
):
    """
    Recursively collects all code files from the specified directories and concatenates them into a single file.
    Focuses on files that are most relevant for code review and LLM context.
    """
    print_progress(f"Processing directories: {', '.join(directories)}", quiet)
    
    # Resolve directories relative to current working directory
    resolved_dirs = [Path(d).resolve() for d in directories]

    # Prepare output file
    output_path = Path(output_file).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as out_f:
        # First, add the directory tree and get the file order
        directory_tree, file_order = create_directory_tree(
            resolved_dirs, exclude_dirs, include_file_extensions,
            max_file_size, max_depth, quiet
        )
        out_f.write(directory_tree)
        out_f.write("\n\n# ======= File Contents =======\n\n")
        
        # Process files in the same order as they appear in the tree
        total_files = len(file_order)
        for idx, file_path in enumerate(file_order, 1):
            # Show progress
            if not quiet:
                print(f"\rProcessing files: {colored(str(idx), 'cyan')}/{colored(str(total_files), 'cyan')}", end="", flush=True)
            
            # Write a header to indicate the start of this file's content
            try:
                relative_path = file_path.relative_to(next(d for d in resolved_dirs if str(file_path).startswith(str(d))).parent)
                out_f.write(f"\n\n# ======= File: {relative_path} =======\n\n")
                
                # Read and append file content
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    out_f.write(content)
                except Exception as e:
                    print_error(f"Error reading {file_path}: {e}", quiet)
                    continue
            except (StopIteration, ValueError):
                print_warning(f"Could not determine relative path for {file_path}", quiet)
                continue
        
        if not quiet:
            print()  # New line after progress
    
    print_progress(f"\nCode snapshot created at: {output_path}", quiet)
    return str(output_path)

def find_cursor_on_windows():
    """
    Find the Cursor executable on Windows by checking common installation locations.
    Returns the path to Cursor.exe if found, None otherwise.
    """
    possible_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Cursor\Cursor.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Cursor\Cursor.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Cursor\Cursor.exe"),
        os.path.expandvars(r"%PROGRAMFILES(X86)%\Cursor\Cursor.exe"),
    ]
    
    for path in possible_paths:
        if os.path.isfile(path):
            return path
    return None

def open_in_editor(file_path, editor='cursor', quiet=False):
    """
    Attempts to open the file in the specified editor with fallback chain.
    Primary: cursor
    Fallback 1: VS Code
    Fallback 2: System default text editor
    """
    # Try the specified editor first
    editor_commands = {
        'cursor': 'cursor',
        'code': 'code',
        'windsurfer': 'windsurfer'
    }
    
    # If editor is cursor, implement the fallback chain
    if editor.lower() == 'cursor':
        editors_to_try = ['cursor', 'code']
        
        # Special handling for Cursor on Windows
        if sys.platform == 'win32' and editors_to_try[0] == 'cursor':
            cursor_path = find_cursor_on_windows()
            if cursor_path:
                try:
                    subprocess.run([cursor_path, file_path], check=True)
                    print_progress(f"Opened {file_path} in Cursor", quiet)
                    return
                except subprocess.CalledProcessError:
                    pass
            # If Cursor not found or failed, continue with fallback chain
            editors_to_try = editors_to_try[1:]  # Remove 'cursor' from fallback chain
        
        # Try remaining editors in the chain
        for ed in editors_to_try:
            if shutil.which(ed) is not None:
                try:
                    subprocess.run([ed, file_path], check=True)
                    print_progress(f"Opened {file_path} in {ed.title()}", quiet)
                    return
                except subprocess.CalledProcessError:
                    continue
        
        # If no editor worked, try system default
        try:
            if sys.platform == 'darwin':  # macOS
                subprocess.run(['open', file_path], check=True)
            elif sys.platform == 'win32':  # Windows
                os.startfile(file_path)
            else:  # Linux and others
                subprocess.run(['xdg-open', file_path], check=True)
            print_progress(f"Opened {file_path} in system default editor", quiet)
            return
        except (subprocess.CalledProcessError, FileNotFoundError, AttributeError):
            print_error(f"Failed to open file in any editor", quiet)
            return
    
    # For non-cursor editors, just try the specified editor
    editor_cmd = editor_commands.get(editor.lower())
    if not editor_cmd:
        print_error(f"Unsupported editor: {editor}. Supported editors are: {', '.join(editor_commands.keys())}", quiet)
        return
    
    if shutil.which(editor_cmd) is not None:
        try:
            subprocess.run([editor_cmd, file_path], check=True)
            print_progress(f"Opened {file_path} in {editor.title()}", quiet)
        except subprocess.CalledProcessError:
            print_error(f"Failed to open in {editor.title()}. Is {editor.title()} running?", quiet)
    else:
        print_warning(f"{editor.title()} command line tool not found. Please make sure {editor.title()} is installed and the command line tool is available.", quiet)

def main():
    parser = argparse.ArgumentParser(
        description='Create a snapshot of code files in specified directories, optimized for LLM context.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-d', '--directories', nargs='+', default=["."],
                      help='List of directories to scan')
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
    parser.add_argument('--editor', choices=['cursor', 'code', 'windsurfer'], default=None,
                      help='Editor to open the snapshot in (default: from config)')
    parser.add_argument('--set-default-editor', choices=['cursor', 'code', 'windsurfer'],
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
    
    # Use values from args or config
    editor = args.editor or get_default_editor()
    extensions = args.extensions or get_default_extensions()
    exclude_dirs = args.exclude_dirs or get_default_exclude_dirs()
    
    output_path = create_code_snapshot(
        directories=args.directories,
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