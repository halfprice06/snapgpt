import sys
import os
import shutil
import signal
from pathlib import Path
from .config import print_warning, print_error, print_progress

def _ignore_sigchld_if_possible():
    if hasattr(signal, 'SIGCHLD'):
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)

def _shell_launch_background(command_str, quiet=False):
    """
    Launch a background process via the OS shell without creating a Python subprocess.Popen handle.
    This avoids the ResourceWarning in Python 3.13+.
    """
    try:
        if sys.platform.startswith('win'):
            # On Windows, 'start /min "" ...' starts a detached process in a minimized window
            os.system(f'start /min "" {command_str}')
        else:
            # On macOS/Linux, use & to background it; redirect to /dev/null so it doesn't keep a terminal open
            # For TextEdit specifically, use -g to prevent focus stealing
            if "open -a TextEdit" in command_str:
                command_str = command_str.replace("open -a TextEdit", "open -g -a TextEdit")
            os.system(f'({command_str}) > /dev/null 2>&1 &')
    except Exception as e:
        if not quiet:
            print_warning(f"Failed to shell-launch '{command_str}': {e}")

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
        ],
        'notepad': [
            r"%WINDIR%\System32\notepad.exe",
            r"%WINDIR%\notepad.exe"
        ]
        # textedit is not a typical Windows editor, so we omit
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
    Attempt to open a file in the specified editor on Windows.
    We do NOT keep a Python handle to the process -> no ResourceWarning.
    """
    # Try to find a direct path to the editor .exe
    editor_path = find_editor_on_windows(editor)
    abs_file_path = os.path.abspath(file_path)
    if editor_path and os.path.isfile(editor_path):
        # Use a shell command: "start "" <editor_path> <file_path>"
        quoted_editor = f'"{editor_path}"'
        quoted_file = f'"{abs_file_path}"'
        _shell_launch_background(f'{quoted_editor} {quoted_file}', quiet=quiet)
        print_progress(f"Opened {file_path} in {editor.title()}", quiet)
        return True

    # Fallbacks:
    if editor == 'cursor':
        # Cursor might have a CLI-based approach. We can attempt: "node cli.js <path>" 
        # But let's do the same shell approach:
        # e.g. "start "" node C:\Users\You\AppData\Local\Programs\Cursor\resources\app\out\cli.js <file>"
        cli_path = os.path.expandvars(
            r"%LOCALAPPDATA%\Programs\Cursor\resources\app\out\cli.js"
        )
        if os.path.isfile(cli_path):
            cmd_str = f'node "{cli_path}" "{abs_file_path}"'
            _shell_launch_background(cmd_str, quiet=quiet)
            print_progress(f"Opened {file_path} in Cursor (CLI fallback)", quiet)
            return True

    if editor == 'notepad':
        # Just call 'notepad <file>'
        _shell_launch_background(f'notepad "{abs_file_path}"', quiet=quiet)
        print_progress(f"Opened {file_path} in Notepad", quiet)
        return True

    # If all else fails, warn
    if not quiet:
        print_warning(f"Could not open {editor.title()}. Please make sure it's installed correctly.")
    return False

def find_editor_path(editor: str) -> str:
    """
    Attempt to locate the specified editor on macOS/Linux via PATH or known install paths.
    """
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
        ],
        'textedit': [
            '/System/Applications/TextEdit.app/Contents/MacOS/TextEdit',
            '/Applications/TextEdit.app/Contents/MacOS/TextEdit'
        ]
    }

    if editor not in editor_paths:
        print_warning(f"Editor {editor} not in known macOS/Linux paths")
        return None

    # textedit won't be found in PATH, but for others we can try which
    if editor != 'textedit':
        path_cmd = shutil.which(editor)
        if path_cmd:
            print_progress(f"Found {editor} in PATH: {path_cmd}")
            return path_cmd

    # fallback to known paths
    for path in editor_paths[editor]:
        expanded_path = os.path.expanduser(path)
        if os.path.isfile(expanded_path):
            print_progress(f"Found {editor} at: {expanded_path}")
            return expanded_path

    print_warning(f"Could not find {editor} in any expected location")
    return None

def open_in_editor(file_path, editor='cursor', quiet=False):
    """
    Open the snapshot on:
      - Windows: user-chosen editor (plus Notepad fallback).
      - macOS/Linux: user-chosen editor, or fallback to system open.
    We do not store a subprocess handle in Python -> no ResourceWarning.
    """
    if sys.platform == 'win32':
        # Windows: try the chosen editor
        success = try_open_in_editor_windows(editor, file_path, quiet=quiet)
        # Also open Notepad in the background to mirror old behavior
        try_open_in_editor_windows("notepad", file_path, quiet=quiet)
        return

    if sys.platform != 'win32':
        _ignore_sigchld_if_possible()

    editor = editor.lower()
    print_progress(f"Attempting to open with editor: {editor}", quiet=quiet)
    abs_file_path = os.path.abspath(file_path)

    if editor == 'xcode' and sys.platform != 'darwin':
        print_error("Xcode is only available on macOS", quiet)
        return

    # If user specifically wants textedit on mac:
    if editor == 'textedit' and sys.platform == 'darwin':
        # We'll do: open -a TextEdit <file> in the background
        _shell_launch_background(f'open -a TextEdit "{abs_file_path}"', quiet=quiet)
        print_progress(f"Opened {file_path} in TextEdit", quiet)
        return

    # Non-textedit route
    editor_path = find_editor_path(editor)
    if editor_path and os.path.isfile(editor_path):
        # Attempt direct shell launch (backgrounded)
        # e.g. '(<editor_path> "<abs_file_path>") &' on mac/linux
        # or 'start "" <editor_path> <file_path>' on Windows (though we handled that separately)
        _shell_launch_background(f'"{editor_path}" "{abs_file_path}"', quiet=quiet)
        print_progress(f"Opened {file_path} in {editor.title()}", quiet)
        return

    # Mac/Linux fallback: system open
    if sys.platform == 'darwin':
        _shell_launch_background(f'open "{abs_file_path}"', quiet=quiet)
        print_progress(f"Opened {file_path} in system default (macOS)", quiet)
    else:
        # e.g. Linux fallback
        if shutil.which('xdg-open'):
            _shell_launch_background(f'xdg-open "{abs_file_path}"', quiet=quiet)
            print_progress(f"Opened {file_path} in system default (xdg-open)", quiet)
        else:
            print_error("No known way to open file. Install xdg-open or specify a known editor.", quiet)

def refresh_textedit_in_background(file_path: str, quiet: bool = False):
    """
    Force TextEdit on macOS to close & reopen `file_path` without stealing focus.
    If you do this, you'll see no ResourceWarning because we shell out the commands.
    """
    if sys.platform == 'darwin':
        import subprocess
        from pathlib import Path
        try:
            file_name = Path(file_path).name
            applescript = f'''
            tell application "TextEdit"
                set docs to every document whose name is "{file_name}"
                repeat with d in docs
                    close d saving no
                end repeat
                open POSIX file "{file_path}"
            end tell

            tell application "System Events"
                set frontProcess to first process whose frontmost is true
                set frontAppName to name of frontProcess
                if frontAppName is "TextEdit" then
                    set frontmost of process "TextEdit" to false
                end if
            end tell
            '''
            # We can just do a one-shot call to osascript. No persistent Python child process.
            subprocess.run(["osascript", "-e", applescript], check=True)
            print_progress(f"Forcibly reloaded {file_path} in TextEdit (background)", quiet)
        except subprocess.SubprocessError:
            print_error("Failed to forcibly reload in TextEdit (background)", quiet)