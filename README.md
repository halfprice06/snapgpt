# SnapGPT

SnapGPT is a command-line utility that creates a single, well-organized snapshot of your codebase. It's especially handy for sharing your project context with AI coding assistants (like ChatGPT) while keeping your code local. By default it automatically opens the snapshotted code file in Cursor so that on the ChatGPT Desktop app your code repository is 'autofocused' and you can start asking ChatGPT questions right away, no copy and pasting required. You can configure it to open in other editors as well.


SnapGPT crawls through your directories, gathers all relevant code files (based on your config and preferences), and concatenates them into one text file for easy reading or chat-pasting.

## Table of Contents
* [Features](#features)
* [Installation](#installation)
* [Quick Start](#quick-start)
* [Usage](#usage)
* [Common Options](#common-options)
* [Example Commands](#example-commands)
* [Configuration](#configuration)
* [Privacy and Security](#privacy-and-security)
* [Troubleshooting](#troubleshooting)
* [Contributing](#contributing)
* [License](#license)

## Features
* Collect code from multiple directories into a single output file
* Automatically exclude certain directories (e.g., `__pycache__`, `.git`, `node_modules`)
* Configurable file extensions (e.g., `.py`, `.js`, `.tsx`) so you can include what you want
* Auto-open the snapshot in an editor of your choice (Cursor, VS Code, Windsurfer)
* Lightweight and zero external dependencies beyond a few Python libraries
* No network calls: SnapGPT does not upload your code anywhere

## Installation

Requires Python 3.7+  
Tested on Linux, macOS, and Windows.

Install SnapGPT directly from PyPI:

```bash
pip install snapgpt
```

Or if you prefer user-level install:

```bash
pip install --user snapgpt
```

## Quick Start

From your project directory, run:

```bash
snapgpt
```

By default, SnapGPT will:
1. Recursively scan the current directory (.)
2. Exclude folders such as `__pycache__`, `.git`, `node_modules`, etc.
3. Include files with extensions like `.py`, `.js`, `.md`, `.json`, and more
4. Save everything to `full_code_snapshot.txt`
5. Open that file in your default editor (configured in `~/.config/snapgpt/config.json`)

Done! You'll see a directory tree at the top of `full_code_snapshot.txt`, followed by the full text of every included file.

## Usage

```bash
snapgpt [options]
```

## Common Options
* `-d, --directories`: List of directories to scan (default: .)
* `-o, --output`: Output file path (default: full_code_snapshot.txt)
* `-e, --extensions`: File extensions to include (e.g. `-e .py .js .md`)
* `--exclude-dirs`: Directories to exclude (e.g. `--exclude-dirs .git node_modules`)
* `--no-open`: Do not automatically open the snapshot after creation
* `--editor {cursor,code,windsurfer}`: Editor to open the snapshot in (overrides config)
* `--set-default-editor`: Set the default editor globally, then exit
* `--set-default-extensions`: Set the default file extensions globally, then exit
* `--set-default-exclude-dirs`: Set the default excluded directories globally, then exit
* `--max-size`: Maximum file size in MB to include (0 for no limit)
* `--max-depth`: Maximum directory depth to traverse (0 for no limit)
* `-q, --quiet`: Suppress progress and non-error messages

## Example Commands

1. Scan only the src and lib directories, exclude dist:
```bash
snapgpt -d src lib --exclude-dirs dist
```

2. Include only Python and Markdown files, skip opening the result:
```bash
snapgpt --extensions .py .md --no-open
```

3. Set default editor to VS Code, then quit (no snapshot creation):
```bash
snapgpt --set-default-editor code
```

4. Use a max file size limit of 1 MB (1,000,000 bytes) and a max depth of 5 subdirectories:
```bash
snapgpt --max-size 1 --max-depth 5
```

## Configuration

SnapGPT reads configuration from `~/.config/snapgpt/config.json`, which is auto-created with defaults the first time you run SnapGPT.

Example config (simplified):
```json
{
  "default_editor": "cursor",
  "file_extensions": [".py", ".js", ".ts", ".md", ".json"],
  "exclude_dirs": ["__pycache__", ".git", "node_modules", "build"]
}
```

You can update these values persistently using:
* `snapgpt --set-default-editor [cursor|code|windsurfer]`
* `snapgpt --set-default-extensions .py .js .md`
* `snapgpt --set-default-exclude-dirs .git node_modules build`

## Privacy and Security
* **Local Only**: SnapGPT does not send your code to any external server or service. It simply reads files from your disk and consolidates them into a single text file.
* **Editor Launch**: If you choose to open the snapshot automatically, SnapGPT will launch your local editor. No additional code upload or syncing occurs.

## Troubleshooting

### 1. Command Not Found
Make sure you installed SnapGPT in a directory on your PATH. Try:
```bash
pip show snapgpt
```
If it's not in your PATH, you may need to use `python -m snapgpt ...` or add the script's location to your PATH.

### 2. Permission Denied
On some systems, certain directories may be locked down. SnapGPT will skip unreadable directories and display a warning.

### 3. No Files Found
If your project has unusual file extensions, add them with `--extensions .mjs .hbs` or via the default config.

### 4. Editor Not Opening
Confirm your chosen editor (Cursor, VS Code, or Windsurfer) is installed and accessible from the command line.

## Contributing

Contributions welcome! If you have ideas for new features or find a bug:
1. Fork the repo and create a branch for your changes
2. Submit a pull request with a clear explanation and relevant details
3. We'll review and merge if it aligns with the project's goals

Please ensure your code follows best practices and is well-documented.

## License

This project is licensed under the MIT License. Feel free to use, modify, and distribute the code in accordance with the license terms.

Happy snapping! If you have any questions or feedback, feel free to open an issue or start a discussion.