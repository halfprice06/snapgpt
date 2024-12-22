# SnapGPT 📸

SnapGPT is a command-line utility that streamlines sharing your codebase with ChatGPT. When run from your project's directory, it creates a single, organized snapshot file (working_snapshot.md) containing all your relevant code. Designed specifically for the ChatGPT Desktop app on MacOS, it automatically opens this snapshot in TextEdit and integrates with ChatGPT's o1 and o1-pro features. No manual copying required—just run SnapGPT and start chatting with AI about your code. If you run SnapGPT in 'watch' mode, it will also automaticlaly update the working_snapshot.md file as you code so the ChatGPT Desktop app will always have the latest version of your codebase.

Just click the [Work With Button](https://github.com/halfprice06/snapgpt/assets/work-with-button.png) to pair with TextEditin the ChatGPT Desktop App and SnapGPT will do the rest.

SnapGPT offers two modes:

* **Default Mode**: A snapshot of your codebase is created when you run 'snapgpt' in the terminal and opened inside TextEdit.

* **Watch Mode**: Automatically updates your snapshot as you code using the watchdog library. Continues to watch until you stop it with Ctrl+C.

For example:

```bash
snapgpt watch
```

The following are my suggested custom instructions for the ChatGPT Desktop App to pair with TextEdit and a coding IDE like Cursor:

``` bash
You are a coding assitant. Unless directed otherwise, you are going to be given the snapshot of the current working code base or project repository. You may not be given every file. 

When the user asks for changes, if the changes involve more than just a couple simple methods, always return the entire file or files that need to be changed so the user can copy and paste them into their ide. 

For simple changes that involve small portions of a single file or a few methods from a few files, instead return explicit instructions that you are giving to a smaller ‘work horse’ model that will implement your changes. Your instructions to that model must be comprehensive such that the model can take your instructions nad implement all changes on its own. 

When you respond, always specify to the user whether you are giving them full code files to copy and paste or whether you are giving instructions to the work horse agent. 

When giving the work horse agent instructions, give all of the instructions in a single code block so it’s easily and copy and pasted to the work horse agent.
```

In either mode, SnapGPT crawls through your directories, gathers all relevant code files (based on your config and preferences), and concatenates them into one text file for easy reading or chat-pasting.

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

After install, simply run in the repo or directory you want to snapshot:
```bash
snapgpt
```

By default, SnapGPT will:
1. Recursively scan the current directory (`.`).
2. Exclude folders such as __pycache__, .git, node_modules, etc.
3. Include files with extensions like .py, .js, .md, .json, and more.
4. Save everything to working_snapshot.md.
5. Open that file in your chosen editor.
6. Copy the content to your clipboard (if enabled).

You will see:
1. A directory tree at the top of working_snapshot.md.
2. Followed by the full text of every included file, separated by headers indicating file paths.

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

Watch Mode uses the watchdog library to watch your project folder in real-time. When you run:

```bash
snapgpt watch
```

SnapGPT will:
1. Perform an initial incremental snapshot of your code (creating or updating working_snapshot.md).
2. Stay running in the terminal, listening for filesystem changes (adds, edits, deletes).
3. Update working_snapshot.md automatically whenever you modify a file that's tracked by SnapGPT.

Press Ctrl+C to stop watching.

If you need to run SnapGPT in the background, consider using tools like tmux, screen, or your system's background job features, but typically watch mode is run in a dedicated terminal window.

### Performance & Debouncing

SnapGPT "debounces" change events with a short delay (about 1 second by default) to avoid regenerating the snapshot multiple times if a file is changing rapidly. Each time you save a file, SnapGPT will wait one second after the last change before regenerating the snapshot.

### Stopping Watch Mode

Simply press Ctrl+C in the terminal to end the watch process. SnapGPT will print a message indicating the watcher is stopping, and then the process will exit.

## Common Options 🛠️

| Option / Flag | Description |
|--------------|-------------|
| -d, --directories | List of directories to scan (default: .) |
| -f, --files | List of specific files to include (overrides directory scanning) |
| -o, --output | Output file path (default: working_snapshot.md) |
| -e, --extensions | File extensions to include (e.g. -e .py .js .md) |
| --exclude-dirs | Directories to exclude from scanning |
| --max-size | Maximum file size in MB to include (0 for no limit) |
| --max-depth | Maximum directory depth to traverse (0 for no limit) |
| -q, --quiet | Suppress progress and non-error messages |
| --no-copy | Do not copy the snapshot to clipboard |
| --set-default-editor | Set the default editor globally |
| --set-default-extensions | Set the default file extensions globally |
| --set-default-exclude-dirs | Set the default excluded directories globally |

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
snapgpt watch -d . --output live_snapshot.md
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
- Using command-line flags like --set-default-editor and --no-copy
- By directly editing the config file

## Contributing 🤝

Contributions are welcome! If you have ideas for new features or find a bug:
1. Fork the repo and create a branch for your changes
2. Submit a pull request with a clear explanation and relevant details
3. We'll review and merge if it aligns with the project's goals

Please ensure your code follows best practices and is well-documented.

## License 📄

This project is licensed under the MIT License. Feel free to use, modify, and distribute the code in accordance with the license terms.

Happy snapping! 🎉 If you have any questions or feedback, feel free to open an issue or start a discussion.
