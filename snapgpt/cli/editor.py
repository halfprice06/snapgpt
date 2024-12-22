import sys
import os
import subprocess
import shutil
import signal
from pathlib import Path
from .config import print_warning, print_error, print_progress

def _ignore_sigchld_if_possible():
    if hasattr(signal, 'SIGCHLD'):
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)

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
    Uses DETACHED_PROCESS so the subprocess won't block SnapGPT.
    Returns True if successful, False otherwise.
    """
    editor_path = find_editor_on_windows(editor)
    if editor_path and editor_path.lower().endswith(f'{editor}.exe'):
        try:
            abs_file_path = os.path.abspath(file_path)
            kwargs = {
                'stdin': subprocess.DEVNULL,
                'stdout': subprocess.DEVNULL,
                'stderr': subprocess.DEVNULL,
                'creationflags': subprocess.DETACHED_PROCESS
            }
            p = subprocess.Popen([editor_path, abs_file_path], **kwargs)
            # Close out references to avoid Python 3.13 ResourceWarning
            if p.stdin:
                p.stdin.close()
            if p.stdout:
                p.stdout.close()
            if p.stderr:
                p.stderr.close()

            print_progress(f"Opened {file_path} in {editor.title()}", quiet)
            return True
        except (subprocess.SubprocessError, OSError):
            # If that fails, try using Cursor CLI logic if editor == 'cursor'
            if editor == 'cursor':
                cli_path = os.path.expandvars(
                    r"%LOCALAPPDATA%\Programs\Cursor\resources\app\out\cli.js"
                )
                if os.path.isfile(cli_path):
                    try:
                        kwargs = {
                            'stdin': subprocess.DEVNULL,
                            'stdout': subprocess.DEVNULL,
                            'stderr': subprocess.DEVNULL,
                            'creationflags': subprocess.DETACHED_PROCESS
                        }
                        p = subprocess.Popen(['node', cli_path, abs_file_path], **kwargs)
                        # Close descriptors
                        if p.stdin:
                            p.stdin.close()
                        if p.stdout:
                            p.stdout.close()
                        if p.stderr:
                            p.stderr.close()
                        
                        print_progress(f"Opened {file_path} in {editor.title()} using CLI", quiet)
                        return True
                    except (subprocess.SubprocessError, OSError):
                        pass
    if not quiet:
        print_warning(f"Could not open {editor.title()}. Please make sure it is installed correctly.")
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
            # For macOS 13+ (Ventura)
            '/System/Applications/TextEdit.app/Contents/MacOS/TextEdit',
            # For older macOS
            '/Applications/TextEdit.app/Contents/MacOS/TextEdit'
        ]
    }

    if editor not in editor_paths:
        print_warning(f"Editor {editor} not in known paths")
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
        else:
            print_warning(f"Tried {editor} at: {expanded_path} (not found)")

    print_warning(f"Could not find {editor} in any expected location")
    return None


def open_in_editor(file_path, editor='cursor', quiet=False):
    """
    Open the given file in the specified editor.
    Fully detach the editor process so Python won't track it as a child.
    """
    if sys.platform != 'win32':
        _ignore_sigchld_if_possible()

    editor = editor.lower()
    print_progress(f"Attempting to open with editor: {editor}", quiet=quiet)
    
    editor_commands = {
        'cursor': 'cursor',
        'code': 'code',
        'windsurf': 'windsurf',
        'zed': 'zed',
        'xcode': 'xed',
        'textedit': 'textedit'
    }
    if editor == 'xcode' and sys.platform != 'darwin':
        print_error("Xcode is only available on macOS", quiet)
        return

    # On Windows, try a Windows-specific approach
    if sys.platform == 'win32' and editor in ['cursor', 'code', 'windsurf', 'zed']:
        if try_open_in_editor_windows(editor, file_path, quiet):
            return

    # If user specifically wants textedit on mac/linux:
    if editor == 'textedit' and sys.platform == 'darwin':
        abs_file_path = os.path.abspath(file_path)
        kwargs = {
            'stdin': subprocess.DEVNULL,
            'stdout': subprocess.DEVNULL,
            'stderr': subprocess.DEVNULL,
            'start_new_session': True
        }
        try:
            # direct "open -a TextEdit" also works, but we'll use the path found
            textedit_path = find_editor_path('textedit')
            if textedit_path and os.path.isfile(textedit_path):
                p = subprocess.Popen(['open', '-a', 'TextEdit', abs_file_path], **kwargs)
                if p.stdin:
                    p.stdin.close()
                if p.stdout:
                    p.stdout.close()
                if p.stderr:
                    p.stderr.close()
                print_progress(f"Opened {file_path} in TextEdit", quiet)
                return
            else:
                # fallback: system open
                subprocess.run(['open', abs_file_path], check=True)
                print_progress(f"Opened {file_path} via system open (TextEdit fallback)", quiet)
                return
        except (subprocess.SubprocessError, OSError) as e:
            print_warning(f"Failed to open with TextEdit: {str(e)}")
            # final fallback
            try:
                subprocess.run(['open', abs_file_path], check=True)
                print_progress(f"Opened {file_path} in system default editor", quiet)
            except (subprocess.SubprocessError, FileNotFoundError):
                print_error("Failed to open file in any editor", quiet)
        return

    # Otherwise, proceed with the general method
    editor_path = find_editor_path(editor)
    if not editor_path:
        # Try fallback editors if the requested one isn't found
        for fallback in ['cursor', 'code', 'windsurf', 'zed']:
            if fallback != editor:
                print_progress(f"Trying fallback editor: {fallback}", quiet)
                fallback_path = find_editor_path(fallback)
                if fallback_path:
                    print_progress(f"Using fallback editor: {fallback}", quiet)
                    editor = fallback
                    editor_path = fallback_path
                    break

    # If we found a path or fallback, attempt to launch
    if editor_path:
        try:
            abs_file_path = os.path.abspath(file_path)
            kwargs = {
                'stdin': subprocess.DEVNULL,
                'stdout': subprocess.DEVNULL,
                'stderr': subprocess.DEVNULL
            }
            # Windows uses DETACHED_PROCESS
            if sys.platform == 'win32':
                kwargs['creationflags'] = subprocess.DETACHED_PROCESS
            else:
                # macOS/Linux: fully detach with start_new_session=True
                kwargs['start_new_session'] = True

            # On macOS, if not using xcode or textedit, we either do a direct spawn or 'open -a'...
            if sys.platform == 'darwin' and editor not in ['xcode', 'textedit']:
                if '.app/Contents/MacOS' in editor_path:
                    app_root = editor_path.split('/Contents/MacOS/')[0]
                    p = subprocess.Popen(['open', '-a', app_root, abs_file_path], **kwargs)
                    if p.stdin:
                        p.stdin.close()
                    if p.stdout:
                        p.stdout.close()
                    if p.stderr:
                        p.stderr.close()
                else:
                    p = subprocess.Popen([editor_path, abs_file_path], **kwargs)
                    if p.stdin:
                        p.stdin.close()
                    if p.stdout:
                        p.stdout.close()
                    if p.stderr:
                        p.stderr.close()
            else:
                # Linux, or xcode on mac
                p = subprocess.Popen([editor_path, abs_file_path], **kwargs)
                if p.stdin:
                    p.stdin.close()
                if p.stdout:
                    p.stdout.close()
                if p.stderr:
                    p.stderr.close()

            print_progress(f"Opened {file_path} in {editor.title()}", quiet)
            return
        except (subprocess.SubprocessError, OSError) as e:
            print_warning(f"Failed to open with {editor}: {str(e)}")

    # Final fallback: system default
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


def refresh_textedit_in_background(file_path: str, quiet: bool = False):
    """
    Force TextEdit to close and reopen `file_path` without stealing focus (macOS).
    NOTE: This discards any unsaved changes in TextEdit for that file.
    """
    if sys.platform == 'darwin':
        import subprocess
        from pathlib import Path
        try:
            file_name = Path(file_path).name
            applescript = f'''
            tell application "TextEdit"
                -- Close matching documents (discarding changes)
                set docs to every document whose name is "{file_name}"
                repeat with d in docs
                    close d saving no
                end repeat
                -- Open again
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
            subprocess.run(["osascript", "-e", applescript], check=True)
            print_progress(f"Forcibly reloaded {file_path} in TextEdit (background)", quiet)
        except subprocess.SubprocessError:
            print_error("Failed to forcibly reload in TextEdit (background)", quiet)