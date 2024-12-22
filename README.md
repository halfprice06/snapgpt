# SnapGPT 📸

SnapGPT is a command-line utility that creates a single, organized snapshot of your codebase for ChatGPT. Perfect for quickly sharing your work in the ChatGPT Desktop App (particularly on macOS), it opens a unified snapshot of your project (called `working_snapshot.md`) in TextEdit and seamlessly integrates with ChatGPT's code features—no manual copy-pasting required.

It's recommended you use the following custom instruction in your ChatGPT settings so that when ChatGPT recommends code changes it's easy to reapply them in your AI IDE. You'll either get back full files to copy and paste or a set of custom instructions you can paste to the Chat or "Agent" inside your IDE, like 'agent' in Cursor.

```plaintext

You are a coding assitant. Unless directed otherwise, you are going to be given the snapshot of the current working code base or project repository. You may not be given every file. 

When the user asks for changes, if the changes involve more than just a couple simple methods, always return the entire file or files that need to be changed so the user can copy and paste them into their ide. 

For simple changes that involve small portions of a single file or a few methods from a few files, instead return explicit instructions that you are giving to a smaller ‘work horse’ model that will implement your changes. Your instructions to that model must be comprehensive such that the model can take your instructions nad implement all changes on its own. 

When you respond, always specify to the user whether you are giving them full code files to copy and paste or whether you are giving instructions to the work horse agent. 

When giving the work horse agent instructions, give all of the instructions in a single code block so it’s easily and copy and pasted to the work horse agent.
```

---

## Overview

When run from your project's root directory, SnapGPT does the following:

1. Recursively scans the current directory.
2. Skips typically unimportant folders like `__pycache__`, `.git`, `node_modules`, etc.
3. Collects files with useful extensions (`.py`, `.js`, `.ts`, `.md`, `.json`, and more).
4. Generates a single file (`working_snapshot.md`) containing:
   - A directory tree at the top (for easy reference).
   - The text of every included file, separated by headers.

By default, it then:
1. Opens `working_snapshot.md` in your editor (e.g., TextEdit on macOS).
3. Integrates with ChatGPT Desktop App features—just press the "Work With" button in ChatGPT, pick TextEdit, and SnapGPT has your code ready to go!

---

## Features

- **Single, Organized Snapshot**: Combine all relevant code and markdown files into one text file. 

- **Automatic Editor Opening**: After generating the snapshot, it opens automatically in TexEdit or Notepad on Windows and also in your IDE of choice. 

- **Incremental Scanning**: Only re-scan changed files, making repeated snapshots quick and efficient, even for large codebases.

- **Watch Mode**: Stay running in the terminal to detect changes on the fly. If you modify your code, SnapGPT instantly updates the snapshot — useful for live collaboration with ChatGPT.

- **Flexible Configuration**: Control which files and directories are included, specify max depth, max file size, and more.

---

## Installation

### macOS (Recommended)

#### Using Homebrew
```bash
brew install halfprice06/homebrew-tap-snapgpt/snapgpt
```

#### Using pipx

```bash
# Install pipx if you haven't already
brew install pipx
pipx ensurepath

# Install snapgpt
pipx install snapgpt
```

### Other Methods

#### Using pip

```bash
pip install --user snapgpt
```

#### Using a virtual environment

```bash
python3 -m venv myenv
source myenv/bin/activate
pip install snapgpt
```

## Usage

Run `snapgpt` in any directory to produce `working_snapshot.md`. SnapGPT offers two main modes:

### Default (Incremental) Mode

```bash
snapgpt
```

- Creates (or updates) a snapshot of your code using incremental scanning.
- Only re-hashes changed files, speeding up repeated snapshots significantly.
- Opens the resulting file in your editor (by default, TextEdit on macOS).

### Watch Mode

```bash
snapgpt watch
```

- Continually monitors your project for filesystem changes.
- Whenever you save or modify a file, SnapGPT updates `working_snapshot.md` automatically.
- Stays running until you press Ctrl+C.

### Watch Mode Details

- **Real-Time Monitoring**: Uses the watchdog library to detect add/edit/delete events.
- **Debouncing**: Waits about 1 second after the last file change before regenerating the snapshot (useful if your editor saves repeatedly).
- **Stopping**: Press Ctrl+C to end watch mode. SnapGPT will finalize and exit.

## Common Options

| Option / Flag | Description |
|--------------|-------------|
| -d, --directories | Directories to scan (default: .) |
| -f, --files | Specific files to include (overrides dir scanning) |
| -o, --output | Output file path (default: working_snapshot.md) |
| -e, --extensions | File extensions to include (e.g. -e .py .js .md) |
| --exclude-dirs | Directories to exclude from scanning |
| --max-size | Maximum file size in MB (0 for no limit) |
| --max-depth | Maximum directory depth (0 for no limit) |
| -q, --quiet | Suppress progress/output messages |
| --no-copy | Disable copying snapshot content to clipboard |
| --set-default-editor | Configure a global default IDE (e.g. code, cursor) |
| --set-default-extensions | Set default file extensions globally |
| --set-default-exclude-dirs | Set default excluded directories globally |

## Example Commands

1. Include specific files only:
```bash
snapgpt -f src/main.py tests/test_main.py README.md
```

2. Scan only the src and lib directories, exclude dist:
```bash
snapgpt -d src lib --exclude-dirs dist
```

3. Change default editor to VS Code and exit:
```bash
snapgpt --set-default-editor code
```

4. Limit file size to 1MB and directory depth to 5:
```bash
snapgpt --max-size 1 --max-depth 5
```

5. Watch mode with a custom output file:
```bash
snapgpt watch -d . --output live_snapshot.md
```

## Configuration

SnapGPT stores your settings in `~/.config/snapgpt/config.json`. During first-time setup, you can choose:
- Editor: cursor, code, windsurf, zed, xcode, or textedit
- Auto copy: Whether SnapGPT should automatically copy the snapshot content to your clipboard.

You can always override these defaults using command-line flags or by manually editing the config file:

```json
{
  "default_editor": "cursor",
  "auto_copy_to_clipboard": true,
  "first_time_setup_done": true,
  "file_extensions": [".py", ".js", ".ts", ".md", ".json", ...],
  "exclude_dirs": ["__pycache__", ".git", "node_modules", "build"]
}
```

## Contributing

Contributions are welcome! Feel free to open an issue or start a discussion for questions, ideas, or bug reports. To contribute:
1. Fork the repository.
2. Create a branch for your feature or fix.
3. Commit with clear explanations.
4. Submit a Pull Request and we'll review ASAP.

## License

SnapGPT is licensed under the MIT License. You are free to use, modify, and distribute the code, subject to the license terms.

## Support & Feedback

If you have any questions, encounter bugs, or just want to share feedback, please open an issue or start a discussion. We'd love to hear from you—happy snapping!