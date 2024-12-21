# SnapGPT 📸

SnapGPT is a command-line utility that creates a single, well-organized snapshot of your codebase. It's especially handy for sharing your project context with AI coding assistants (like ChatGPT) while keeping your code local. By default, SnapGPT automatically opens the snapshotted code file in **Cursor**, so that on the ChatGPT Desktop app your code repository is "autofocused" and you can start asking ChatGPT questions right away—no copy and pasting required. You can configure it to open in other editors as well (VS Code, Windsurf, Zed, Xcode, or any other editor).

SnapGPT offers two modes:

* **Incremental Mode** (Default): Only re-reads changed files for faster repeated snapshots—ideal for large projects you reference often

* **Watch Mode**: Automatically updates your snapshot as you code—great for active development sessions with AI assistance

```bash
snapgpt watch

In either mode, SnapGPT crawls through your directories, gathers all relevant code files (based on your config and preferences), and concatenates them into one text file for easy reading or chat-pasting.

## Table of Contents
* [Features](#features-)
* [Installation](#installation-)
* [Quick Start](#quick-start-)
* [Usage](#usage-)
* [Watch Mode Details](#watch-mode-details)
* [Common Options](#common-options-)
* [Example Commands](#example-commands-)
* [Configuration](#configuration-)
* [Privacy and Security](#privacy-and-security-)
* [Troubleshooting](#troubleshooting-)
* [Contributing](#contributing-)
* [License](#license-)

## Features ✨
* Collect code from multiple directories into a single output file
* Select specific files to include instead of scanning directories
* Automatically exclude certain directories (e.g., `__pycache__`, `.git`, `node_modules`)
* Smart directory scanning safety:
  * Warns when scanning non-Git directories (helps prevent accidental scanning of non-project folders)
  * Detects and warns about system directories (Windows, macOS, Linux) to prevent accidental system scanning
  * Requires explicit confirmation before scanning sensitive directories
* Incremental scanning:
  * Re-scan your repo faster by only re-reading changed files
  * Maintains a hash index for quick file comparison
  * Perfect for large projects you snapshot frequently
* Watch mode:
  * Automatically updates the snapshot when files change
  * Uses efficient incremental scanning under the hood
  * Great for active development sessions
* Configurable file extensions (e.g., `.py`, `.js`, `.tsx`) so you can include exactly what you want
* Auto-open the snapshot in an editor of your choice (Cursor, VS Code, Windsurf, Zed, Xcode, or fallback to your system default)
* Auto-copy to clipboard - Automatically copy the snapshot to your clipboard (configurable)
* First-time setup wizard - Interactive setup to choose your preferred editor and clipboard settings
* Cross-platform editor support - Improved support for editors across Windows, Mac, and Linux
* Lightweight and has minimal dependencies
* Local only: SnapGPT does not make any network calls, keeping your code fully private

## Installation 🚀

### macOS (Recommended)

Using Homebrew:

```bash
brew install halfprice06/homebrew-tap-snapgpt/snapgpt
```

Using pipx (recommended for Python CLI tools):

```bash
# Install pipx if you haven't already
brew install pipx
pipx ensurepath

# Install snapgpt
pipx install snapgpt
```

### Other Methods:

Using pip:

```bash
pip install --user snapgpt
```

Using a virtual environment:

```bash
python3 -m venv myenv
source myenv/bin/activate
pip install snapgpt
```

SnapGPT requires Python 3.7+.
It is tested on Linux, macOS, and Windows.

## Quick Start 🏃‍

When you run SnapGPT for the first time, you'll be greeted with a setup wizard:

```
Welcome to snapgpt! Let's set up your preferences.

Available editors:
1. Cursor
2. Code
3. Windsurf
4. Zed
5. Xcode

Which editor would you like to use as default? (enter number): 
Would you like snapshots to be automatically copied to clipboard? (y/n): 
```

After setup, simply run:

```bash
snapgpt
```

By default, SnapGPT will:
1. Recursively scan the current directory (`.`)
2. Exclude folders such as `__pycache__`, `.git`, `node_modules`, etc.
3. Include files with extensions like `.py`, `.js`, `.md`, `.json`, and more
4. Save everything to `full_code_snapshot.txt`
5. Open that file in your chosen editor
6. Copy the content to your clipboard (if enabled)

You will see:
1. A directory tree at the top of `full_code_snapshot.txt`
2. Followed by the full text of every included file, separated by headers indicating file paths

This single file is perfect for sharing with ChatGPT or any other AI coding assistant (or just for your own review)!

## Usage 📝

```bash
snapgpt [options]
```

SnapGPT offers two main modes of operation:

1. Default (Incremental) Mode:

```bash
snapgpt
```
Creates a snapshot of your codebase, using incremental scanning to only re-read changed files. This makes repeated snapshots much faster, especially for large codebases.

2. Watch Mode:

```bash
snapgpt watch
```
Continuously monitors your codebase and updates the snapshot whenever files change. (See Watch Mode Details for more info.)

## Watch Mode Details

Watch Mode uses the `watchdog` library to watch your project folder in real-time. When you run:

```bash
snapgpt watch
```

SnapGPT will:
1. Perform an initial incremental snapshot of your code (creating or updating `full_code_snapshot.txt`)
2. Stay running in the terminal, listening for filesystem changes (adds, edits, deletes)
3. Update `full_code_snapshot.txt` automatically whenever you modify a file that's tracked by SnapGPT

Press `Ctrl+C` to stop watching.

If you need to run SnapGPT in the background, consider using tools like `tmux`, `screen`, or your system's background job features, but typically watch mode is run in a dedicated terminal window.

### Requirements

You must have watchdog installed:

```bash
pip install watchdog
```

If you installed SnapGPT via pipx or the included dependencies in `pyproject.toml`, you should already have it. If you see an error about missing watchdog, just install it manually.

### Performance & Debouncing

SnapGPT "debounces" change events with a short delay (about 1 second by default) to avoid regenerating the snapshot multiple times if a file is changing rapidly. Each time you save a file, SnapGPT will wait one second after the last change before regenerating the snapshot.

### Stopping Watch Mode

Simply press `Ctrl+C` in the terminal to end the watch process. SnapGPT will print a message indicating the watcher is stopping, and then the process will exit.

## Common Options 🛠️

| Option / Flag | Description |
|--------------|-------------|
| `-d, --directories` | List of directories to scan (default: .) |
| `-f, --files` | List of specific files to include (overrides directory scanning) |
| `-o, --output` | Output file path (default: full_code_snapshot.txt) |
| `-e, --extensions` | File extensions to include (e.g. -e .py .js .md) |
| `--exclude-dirs` | Directories to exclude from scanning |
| `--max-size` | Maximum file size in MB to include (0 for no limit) |
| `--max-depth` | Maximum directory depth to traverse (0 for no limit) |
| `-q, --quiet` | Suppress progress and non-error messages |
| `--no-copy` | Do not copy the snapshot to clipboard |
| `--set-default-editor` | Set the default editor globally |
| `--set-default-extensions` | Set the default file extensions globally |
| `--set-default-exclude-dirs` | Set the default excluded directories globally |

## Example Commands 💡

1. Include specific files only:

```bash
snapgpt -f src/main.py tests/test_main.py README.md
```

2. Scan only the src and lib directories, exclude dist:

```bash
snapgpt -d src lib --exclude-dirs dist
```

3. Set default editor to VS Code, then quit immediately:

```bash
snapgpt --set-default-editor code
```

4. Use a max file size limit of 1 MB and a max depth of 5 subdirectories:

```bash
snapgpt --max-size 1 --max-depth 5
```

5. Watch mode with custom output file:

```bash
snapgpt watch -d . --output live_snapshot.txt
```

## Configuration ⚙️

SnapGPT reads configuration from `~/.config/snapgpt/config.json`, which is created during first-time setup or with defaults if you skip the setup.

Example config:

```json
{
  "default_editor": "cursor",
  "auto_copy_to_clipboard": true,
  "first_time_setup_done": true,
  "file_extensions": [".py", ".js", ".ts", ".md", ".json"],
  "exclude_dirs": ["__pycache__", ".git", "node_modules", "build"]
}
```

You can update these values:
* Through the first-time setup wizard
* Using command-line flags like `--set-default-editor` and `--no-copy`
* By directly editing the config file

## Privacy and Security 🔒
* Local Only: SnapGPT does not send your code to any external server or service. It simply reads files from your disk and consolidates them into a single text file.
* Editor Launch: If you choose to open the snapshot automatically, SnapGPT will launch your local editor. No additional code upload or syncing occurs.
* Directory Safety Checks:
  * Warns when scanning directories that are not part of a Git repository to prevent accidental scanning of personal folders
  * Detects and warns about system directories on Windows, macOS, and Linux
  * Requires explicit confirmation before proceeding with potentially sensitive directories
  * Default 'no' response in quiet mode for safety

## Troubleshooting 🔧

1. Git Repository Warning
   * When scanning a directory that contains a `.git` folder, SnapGPT will warn you that you might be scanning more files than intended. You can:
     * Choose to continue by typing 'y'
     * Cancel and use more specific paths with `-d` or `-f`
     * Use `--max-depth` to limit the scan depth

2. Command Not Found
   * Make sure you installed SnapGPT in a directory on your PATH. Try:
     ```bash
     pip show snapgpt
     ```
   * If it's not in your PATH, you may need to use `python -m snapgpt ...` or add the script's location to your PATH.

3. Permission Denied
   * On some systems, certain directories may be locked down. SnapGPT will skip unreadable directories and display a warning.

4. No Files Found
   * If your project has unusual file extensions, add them with `--extensions .mjs .hbs` or via the default config.

5. Editor Not Opening
   * Confirm your chosen editor (Cursor, VS Code, Windsurf, Zed, or Xcode) is installed and accessible from the command line.
   * Note that Xcode is only available on macOS systems.
   * On Windows, SnapGPT will attempt various fallback methods if cursor is your default editor but not found in your PATH.

6. Watch Mode Not Working
   * Make sure you have the watchdog package installed:
     ```bash
     pip install watchdog
     ```
   * Then run `snapgpt watch` again.
   * If nothing happens when you save files, double-check that your files have extensions included in your config or in your CLI arguments.

7. Incremental Mode Issues
   * If incremental mode seems incorrect, you can delete the `.snapgpt_index` file in your project directory to force a full rescan.

## Contributing 🤝

Contributions are welcome! If you have ideas for new features or find a bug:
1. Fork the repo and create a branch for your changes
2. Submit a pull request with a clear explanation and relevant details
3. We'll review and merge if it aligns with the project's goals

Please ensure your code follows best practices and is well-documented.

## License 📄

This project is licensed under the MIT License. Feel free to use, modify, and distribute the code in accordance with the license terms.

Happy snapping! 🎉 If you have any questions or feedback, feel free to open an issue or start a discussion.

