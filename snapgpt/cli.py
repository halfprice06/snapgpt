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

# Import the new modules
from .incremental import incremental_snapshot
from .watch import watch_directory

CONFIG_DIR = Path.home() / '.config' / 'snapgpt'
CONFIG_FILE = CONFIG_DIR / 'config.json'

# Default configuration
DEFAULT_CONFIG = {
    'default_editor': 'cursor',
    'auto_copy_to_clipboard': True,
    'first_time_setup_done': False,
    'file_extensions': [
        ".py", ".js", ".ts", ".jsx", ".tsx",
        ".go", ".rs", ".java",
        ".cpp", ".c", ".h",
        ".toml", ".yaml", ".yml", ".json",
        ".md"
    ],
    'exclude_dirs': [
        "__pycache__", "build", "dist", "*.egg-info",
        "venv", ".venv", "env", "node_modules", "vendor", "third_party",
        ".git", ".svn", ".hg",
        ".idea", ".vscode", ".vs",
        ".pytest_cache", ".coverage", "htmlcov",
        "tmp", "temp", ".cache",
        "logs", "log"
    ]
}


def print_warning(msg: str, quiet: bool = False):
    if not quiet:
        cprint(f"\nWarning: {msg}", 'yellow')


def print_error(msg: str, quiet: bool = False):
    if not quiet:
        cprint(f"\nError: {msg}", 'red')


def print_progress(msg: str, quiet: bool = False, end="\n"):
    if not quiet:
        cprint(msg, 'green', end=end)


def get_config():
    """Get configuration from config file, using defaults for missing values."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                config = json.load(f)
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
    return get_config()['default_editor']


def get_default_extensions():
    return get_config()['file_extensions']


def get_default_exclude_dirs():
    return get_config()['exclude_dirs']


def set_default_editor(editor: str, quiet: bool = False) -> bool:
    editor = editor.lower()
    valid_editors = {'cursor', 'code', 'windsurf', 'zed', 'xcode'}

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


def do_first_time_setup(quiet: bool = False) -> None:
    config = get_config()
    if not config.get('first_time_setup_done', False):
        print("\nWelcome to snapgpt! Let's set up your preferences.\n")
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

        while True:
            choice = input("\nWould you like snapshots to be automatically copied to clipboard? (y/n): ").lower()
            if choice in ('y', 'n'):
                config['auto_copy_to_clipboard'] = (choice == 'y')
                break
            print("Please enter 'y' for yes or 'n' for no.")

        config['first_time_setup_done'] = True
        save_config(config)
        print("\nSetup complete! You can change these settings later using command line options.\n")


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
        current = os.path.abspath(path)
        while current != os.path.dirname(current):
            if os.path.exists(os.path.join(current, '.git')):
                return True
            current = os.path.dirname(current)
        return False
    except Exception:
        return False


def find_editor_on_windows(editor: str) -> str:
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
    editor_path = find_editor_on_windows(editor)
    if editor_path and editor_path.lower().endswith(f'{editor}.exe'):
        try:
            current_dir = os.path.dirname(os.path.abspath(file_path))
            abs_file_path = os.path.abspath(file_path)
            with open(os.devnull, 'w') as devnull:
                subprocess.Popen([editor_path, current_dir], stderr=devnull)
                subprocess.Popen([editor_path, abs_file_path], stderr=devnull)
            print_progress(f"Opened {file_path} in {editor.title()}", quiet)
            return True
        except (subprocess.SubprocessError, OSError):
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
    if not quiet:
        print_warning(f"Could not open {editor.title()}. Please make sure it is installed correctly.")
    return False


def find_editor_path(editor: str) -> str:
    if sys.platform == 'win32':
        return find_editor_on_windows(editor)

    editor_paths = {
        'cursor': [
            '/Applications/Cursor.app/Contents/MacOS/Cursor',
            '/usr/bin/cursor',
            '/usr/local/bin/cursor',
            '~/.local/bin/cursor'
        ],
        'code': [
            '/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code',
            '/usr/bin/code',
            '/usr/local/bin/code',
            '~/.local/bin/code'
        ],
        'windsurf': [
            '/Applications/Windsurf.app/Contents/MacOS/Windsurf',
            '/usr/bin/windsurf',
            '/usr/local/bin/windsurf',
            '~/.local/bin/windsurf'
        ],
        'zed': [
            '/Applications/Zed.app/Contents/MacOS/Zed',
            '/usr/bin/zed',
            '/usr/local/bin/zed',
            '~/.local/bin/zed'
        ]
    }

    if editor not in editor_paths:
        return None

    path_cmd = shutil.which(editor)
    if path_cmd:
        return path_cmd

    for path in editor_paths[editor]:
        expanded_path = os.path.expanduser(path)
        if os.path.isfile(expanded_path):
            return expanded_path

    return None


def open_in_editor(file_path, editor='cursor', quiet=False):
    editor = editor.lower()
    editor_commands = {
        'cursor': 'cursor',
        'code': 'code',
        'windsurf': 'windsurf',
        'zed': 'zed',
        'xcode': 'xed'
    }
    if editor == 'xcode' and sys.platform != 'darwin':
        print_error("Xcode is only available on macOS", quiet)
        return

    if sys.platform == 'win32' and editor in ['cursor', 'code', 'windsurf', 'zed']:
        if try_open_in_editor_windows(editor, file_path, quiet):
            return

    editor_cmd = editor_commands.get(editor)
    if not editor_cmd:
        print_error(f"Unsupported editor: {editor}.", quiet)
        return

    editor_path = find_editor_path(editor)
    if editor_path:
        try:
            current_dir = os.path.dirname(os.path.abspath(file_path))
            abs_file_path = os.path.abspath(file_path)
            if sys.platform == 'darwin' and editor != 'xcode':
                if '.app/Contents/MacOS' in editor_path:
                    with open(os.devnull, 'w') as devnull:
                        subprocess.Popen(['open', '-a', editor_path.split('/Contents/MacOS/')[0], current_dir], stderr=devnull)
                        subprocess.Popen(['open', '-a', editor_path.split('/Contents/MacOS/')[0], abs_file_path], stderr=devnull)
                else:
                    with open(os.devnull, 'w') as devnull:
                        subprocess.Popen([editor_path, current_dir], stderr=devnull)
                        subprocess.Popen([editor_path, abs_file_path], stderr=devnull)
            else:
                with open(os.devnull, 'w') as devnull:
                    subprocess.Popen([editor_path, current_dir], stderr=devnull)
                    subprocess.Popen([editor_path, abs_file_path], stderr=devnull)
            print_progress(f"Opened {file_path} in {editor.title()}", quiet)
            return
        except (subprocess.SubprocessError, OSError):
            pass

    # Fallback
    try:
        if sys.platform == 'darwin':
            subprocess.run(['open', file_path], check=True)
        elif sys.platform == 'win32':
            os.startfile(file_path)
        else:
            subprocess.run(['xdg-open', file_path], check=True)
        print_progress(f"Opened {file_path} in system default editor", quiet)
    except (subprocess.SubprocessError, FileNotFoundError, AttributeError):
        print_error("Failed to open file in any editor", quiet)


def print_directory_tree_and_get_files(
    directories: list,
    exclude_dirs: Set[str],
    include_file_extensions: Set[str],
    max_file_size: int,
    max_depth: int,
    quiet: bool
) -> Tuple[str, list]:
    """
    A simplified version of the directory tree creation logic.
    Returns (tree_text, file_list).
    """
    file_list = []
    tree_lines = ["# Directory Structure\n"]
    visited = set()

    def valid_dir(d: Path) -> bool:
        for e in exclude_dirs:
            if d.match(e):
                return False
        return True

    def walk(path: Path, depth=0):
        if max_depth > 0 and depth > max_depth:
            return

        if not path.exists():
            return
        if path.is_dir() and not valid_dir(path):
            return

        prefix = "  " * depth
        if path.is_dir():
            tree_lines.append(f"{prefix}- {path.name}/")
            try:
                for item in sorted(path.iterdir()):
                    # Skip hidden, skip excluded
                    if item.name.startswith('.'):
                        continue
                    walk(item, depth + 1)
            except PermissionError:
                pass
        else:
            # It's a file
            tree_lines.append(f"{prefix}- {path.name}")
            if path.suffix.lower() in include_file_extensions:
                size = path.stat().st_size
                if not max_file_size or size <= max_file_size:
                    file_list.append(path)

    for d in directories:
        p = Path(d).resolve()
        if p not in visited:
            visited.add(p)
            walk(p, 0)
        tree_lines.append("")

    return "\n".join(tree_lines), file_list


def generate_snapshot_text(file_paths: list, directory_tree: str) -> str:
    """
    Generate the combined code snapshot text.
    """
    lines = []
    lines.append(directory_tree)
    lines.append("\n# ======= File Contents =======\n")

    for f in file_paths:
        rel_path = f
        # Attempt to find a relative path
        try:
            rel_path = f.relative_to(Path.cwd())
        except ValueError:
            pass
        lines.append(f"\n# ======= File: {rel_path} =======\n")
        try:
            with open(f, 'r', encoding="utf-8", errors="ignore") as fh:
                lines.append(fh.read())
        except Exception as e:
            lines.append(f"# ERROR reading {f}: {e}")

    return "\n".join(lines)


def main():
    do_first_time_setup()

    # Custom formatter class for better help formatting
    class CustomFormatter(argparse.HelpFormatter):
        def __init__(self, prog):
            # Increase width and help position for better alignment
            super().__init__(prog, indent_increment=2, max_help_position=47, width=100)

        def _format_action(self, action):
            # Add extra spacing between sections
            help_text = super()._format_action(action)
            if isinstance(action, argparse._SubParsersAction):
                help_text = '\n' + help_text
            return help_text

        def _format_usage(self, usage, actions, groups, prefix):
            # Customize the usage format
            if prefix is None:
                prefix = 'usage: '
            return super()._format_usage(usage, actions, groups, prefix)

        def _split_lines(self, text, width):
            # Preserve newlines in description
            if text.startswith('\n'):
                return [''] + super()._split_lines(text[1:], width)
            return super()._split_lines(text, width)

    parser = argparse.ArgumentParser(
        description='Create a snapshot of code files in specified directories, optimized for LLM context.',
        formatter_class=CustomFormatter,
        usage='%(prog)s [-h] [-d DIR [DIR ...]] [-f FILE [FILE ...]] [-o FILE]\n' +
              '         [-e EXT [EXT ...]] [--exclude-dirs DIR [DIR ...]] [--max-size MB]\n' +
              '         [--max-depth N] [-q] [--no-copy]\n' +
              '         [--set-default-editor EDITOR] [--set-default-extensions EXT [...]]\n' +
              '         [--set-default-exclude-dirs DIR [...]] [watch]'
    )

    # Base parser arguments (previously in incremental)
    parser.add_argument('-d', '--directories', nargs='+', default=["."],
                        metavar='DIR',
                        help='List of directories to scan')
    parser.add_argument('-f', '--files', nargs='+',
                        metavar='FILE',
                        help='List of specific files to include (overrides directory scanning)')
    parser.add_argument('-o', '--output', default="full_code_snapshot.txt",
                        metavar='FILE',
                        help='Output file path')
    parser.add_argument('-e', '--extensions', nargs='+',
                        default=None,
                        metavar='EXT',
                        help='File extensions to include')
    parser.add_argument('--exclude-dirs', nargs='+', default=None,
                        metavar='DIR',
                        help='Directories to exclude from scanning')
    parser.add_argument('--max-size', type=float, default=0,
                        metavar='MB',
                        help='Maximum file size in MB (0 for no limit)')
    parser.add_argument('--max-depth', type=int, default=0,
                        metavar='N',
                        help='Maximum directory depth (0 for no limit)')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Suppress output')

    # Global settings
    parser.add_argument('--set-default-editor', choices=['cursor', 'code', 'windsurf', 'zed', 'xcode'],
                        metavar='EDITOR',
                        help='Set the default editor and exit')
    parser.add_argument('--set-default-extensions', nargs='+',
                        metavar='EXT',
                        help='Set the default file extensions and exit')
    parser.add_argument('--set-default-exclude-dirs', nargs='+',
                        metavar='DIR',
                        help='Set the default excluded dirs and exit')
    parser.add_argument('--no-copy', action='store_true',
                        help='Do not copy the snapshot to clipboard')

    # Subcommands
    subparsers = parser.add_subparsers(dest='subcommand', title='additional commands')

    # Watch subcommand
    watch_parser = subparsers.add_parser('watch', 
        help='Watch the directory for changes, auto-update snapshot.',
        description='Watch your codebase and automatically update the snapshot when files change.',
        formatter_class=CustomFormatter)
    watch_parser.add_argument('-d', '--directories', nargs='+', default=["."],
                              metavar='DIR',
                              help='List of directories to scan')
    watch_parser.add_argument('-o', '--output', default="full_code_snapshot.txt",
                              metavar='FILE',
                              help='Output file path')
    watch_parser.add_argument('-e', '--extensions', nargs='+', default=None,
                              metavar='EXT',
                              help='File extensions to include')
    watch_parser.add_argument('--exclude-dirs', nargs='+', default=None,
                              metavar='DIR',
                              help='Directories to exclude')
    watch_parser.add_argument('--max-size', type=float, default=0,
                              metavar='MB',
                              help='Max file size in MB')
    watch_parser.add_argument('--max-depth', type=int, default=0,
                              metavar='N',
                              help='Max directory depth')
    watch_parser.add_argument('-q', '--quiet', action='store_true',
                              help='Suppress output')

    args = parser.parse_args()

    # Handle global commands first
    if args.set_default_editor:
        success = set_default_editor(args.set_default_editor, quiet=False)
        sys.exit(0 if success else 1)

    if args.set_default_extensions:
        success = set_default_extensions(args.set_default_extensions, quiet=False)
        sys.exit(0 if success else 1)

    if args.set_default_exclude_dirs:
        success = set_default_exclude_dirs(args.set_default_exclude_dirs, quiet=False)
        sys.exit(0 if success else 1)

    # Possibly disable auto_copy for the run
    if args.no_copy:
        config = get_config()
        config['auto_copy_to_clipboard'] = False
        save_config(config)

    # Shared logic for running the incremental snapshot
    def run_incremental_snapshot(
        directories, files, output_file,
        extensions, exclude_dirs, max_size_mb, max_depth,
        quiet
    ):
        exts = extensions or get_default_extensions()
        exc_dirs = exclude_dirs or get_default_exclude_dirs()
        max_size = int(max_size_mb * 1_000_000) if max_size_mb > 0 else 0

        # Step 1) figure out final file list
        if files:
            final_files = []
            for f in files:
                p = Path(f).resolve()
                if p.exists() and p.suffix.lower() in exts:
                    size = p.stat().st_size
                    if not max_size or size <= max_size:
                        final_files.append(p)
        else:
            _, final_files = print_directory_tree_and_get_files(
                directories, set(exc_dirs), set(e.lower() for e in exts),
                max_size, max_depth, quiet
            )

        # Make sure we confirm scanning non-git or system directories for the first folder
        # (just like in the old code)
        for directory in directories:
            abs_dir = os.path.abspath(directory)
            if is_system_directory(abs_dir):
                print_warning(f"'{directory}' appears to be a system directory.", quiet)
                user_input = input("Do you want to continue? (y/n): ").lower() if not quiet else 'n'
                if user_input != 'y':
                    print_progress("Cancelled.", quiet)
                    sys.exit(0)
            if not is_git_repository(abs_dir):
                print_warning(f"'{directory}' is not part of a Git repo.", quiet)
                user_input = input("Continue? (y/n): ").lower() if not quiet else 'n'
                if user_input != 'y':
                    print_progress("Cancelled.", quiet)
                    sys.exit(0)

        # We define a small function that returns the fully composed text
        def generate_full_text(file_paths):
            # Rebuild directory tree each time for clarity
            d_tree, _ = print_directory_tree_and_get_files(
                directories, set(exc_dirs), set(e.lower() for e in exts),
                max_size, max_depth, quiet
            )
            return generate_snapshot_text(file_paths, d_tree)

        project_root = Path(directories[0]).resolve()
        output_path = Path(output_file).resolve()
        incremental_snapshot(
            project_root=project_root,
            file_paths=final_files,
            output_file=output_path,
            original_snapshot_func=generate_full_text,
            quiet=quiet
        )

        # Optionally open in editor
        editor = get_default_editor()
        open_in_editor(str(output_path), editor, quiet=quiet)

    if not args.subcommand:
        # **Default** to incremental mode
        run_incremental_snapshot(
            directories=["."],
            files=None,
            output_file="full_code_snapshot.txt",
            extensions=None,
            exclude_dirs=None,
            max_size_mb=0,
            max_depth=0,
            quiet=False
        )
        sys.exit(0)

    elif args.subcommand == 'incremental':
        run_incremental_snapshot(
            directories=args.directories,
            files=args.files,
            output_file=args.output,
            extensions=args.extensions,
            exclude_dirs=args.exclude_dirs,
            max_size_mb=args.max_size,
            max_depth=args.max_depth,
            quiet=args.quiet
        )
        sys.exit(0)

    elif args.subcommand == 'watch':
        # watch mode - unchanged from previous
        exts = args.extensions or get_default_extensions()
        exc_dirs = args.exclude_dirs or get_default_exclude_dirs()
        max_size = int(args.max_size * 1_000_000) if args.max_size > 0 else 0
        project_root = Path(args.directories[0]).resolve()
        output_path = Path(args.output).resolve()

        # We'll define a function that re-runs the incremental snapshot each time
        def do_incremental():
            run_incremental_snapshot(
                directories=args.directories,
                files=None,  # Because watch typically scans the entire directory
                output_file=output_path,
                extensions=exts,
                exclude_dirs=exc_dirs,
                max_size_mb=args.max_size,
                max_depth=args.max_depth,
                quiet=args.quiet
            )

        # Run once initially
        do_incremental()

        # Helper: decide if a file is included for watch triggers
        def is_included_func(file_path: Path) -> bool:
            # Extension check
            if file_path.suffix.lower() not in [e.lower() for e in exts]:
                return False
            # Exclude dirs check
            rel_parts = file_path.relative_to(project_root).parts
            for part in rel_parts:
                for exc in exc_dirs:
                    if Path(part).match(exc):
                        return False
            # Size check
            if max_size > 0:
                if file_path.stat().st_size > max_size:
                    return False
            return True

        watch_directory(
            project_root=project_root,
            snapshot_func=do_incremental,
            is_included_func=is_included_func,
            quiet=args.quiet
        )