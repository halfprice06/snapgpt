import sys
from pathlib import Path
from typing import List, Tuple
from termcolor import cprint
from markitdown import MarkItDown

from .config import (
    print_warning, print_progress, get_default_extensions,
    get_default_exclude_dirs, is_system_directory, is_git_repository,
    get_config, save_config
)
from .editor import open_in_editor, refresh_textedit_in_background
from ..incremental import incremental_snapshot
from ..watch import watch_directory

_markitdown_converter = None

def init_markitdown():
    """Initialize the MarkItDown converter if not already initialized."""
    global _markitdown_converter
    if _markitdown_converter is None:
        try:
            _markitdown_converter = MarkItDown()
            return True
        except Exception as e:
            print_warning(f"Failed to initialize MarkItDown: {e}")
            return False
    return True


def print_directory_tree_and_get_files(
    directories: list,
    exclude_dirs: set,
    include_file_extensions: set,
    max_file_size: int,
    max_depth: int,
    quiet: bool,
    excluded_file_path: Path = None
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
        if excluded_file_path and path.resolve() == excluded_file_path.resolve():
            return

        prefix = "  " * depth
        if path.is_dir():
            tree_lines.append(f"{prefix}- {path.name}/")
            try:
                for item in sorted(path.iterdir()):
                    if item.name.startswith('.'):
                        continue
                    walk(item, depth + 1)
            except PermissionError:
                pass
        else:
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
    lines = []
    lines.append(directory_tree)
    lines.append("\n# ======= File Contents =======\n")

    # Use MarkItDown for certain file types (pdf, doc, images, etc)
    markitdown_exts = {
        ".pdf", ".doc", ".docx",
        ".xls", ".xlsx",
        ".ppt", ".pptx",
        ".jpg", ".jpeg", ".png", ".gif",
        ".mp3", ".wav", ".m4a",
        ".csv", ".xml",
        ".zip"
    }

    markitdown_available = init_markitdown()

    for f in file_paths:
        rel_path = f
        try:
            rel_path = f.relative_to(Path.cwd())
        except ValueError:
            pass

        lines.append(f"\n# ======= File: {rel_path} =======\n")
        file_ext = f.suffix.lower()

        if markitdown_available and file_ext in markitdown_exts:
            try:
                converted = _markitdown_converter.convert(str(f))
                if converted and converted.text_content:
                    lines.append(converted.text_content)
                    continue
                else:
                    lines.append(f"# WARNING: MarkItDown conversion returned empty content for {f}")
            except Exception as e:
                lines.append(f"# WARNING: MarkItDown conversion failed for {f}: {str(e)}")
        else:
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    content = file.read()
                    lines.append(content)
            except Exception as e:
                lines.append(f"# ERROR: Could not read file {f}: {str(e)}")

    return "\n".join(lines)


def run_incremental_snapshot(
    directories,
    files,
    output_file,
    extensions,
    exclude_dirs,
    max_size_mb,
    max_depth,
    quiet,
    skip_open_in_editor=False
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
        # We do a "dummy" call to print_directory_tree_and_get_files only to get final_files
        _, final_files = print_directory_tree_and_get_files(
            directories=directories,
            exclude_dirs=set(exc_dirs),
            include_file_extensions=set(e.lower() for e in exts),
            max_file_size=max_size,
            max_depth=max_depth,
            quiet=quiet,
            excluded_file_path=Path(output_file).resolve()
        )

    # Confirm scanning non-git/system directories
    for directory in directories:
        abs_dir = Path(directory).resolve()
        if is_system_directory(str(abs_dir)):
            print_warning(f"'{directory}' appears to be a system directory.", quiet)
            user_input = input("Do you want to continue? (y/n): ").lower() if not quiet else 'n'
            if user_input != 'y':
                print_progress("Cancelled.", quiet)
                sys.exit(0)
        if not is_git_repository(str(abs_dir)):
            print_warning(f"'{directory}' is not part of a Git repo.", quiet)
            user_input = input("Continue? (y/n): ").lower() if not quiet else 'n'
            if user_input != 'y':
                print_progress("Cancelled.", quiet)
                sys.exit(0)

    def generate_full_text(file_paths):
        d_tree, _ = print_directory_tree_and_get_files(
            directories=directories,
            exclude_dirs=set(exc_dirs),
            include_file_extensions=set(e.lower() for e in exts),
            max_file_size=max_size,
            max_depth=max_depth,
            quiet=quiet,
            excluded_file_path=Path(output_file).resolve()
        )
        return generate_snapshot_text(file_paths, d_tree)

    project_root = Path(directories[0]).resolve()
    output_path = Path(output_file).resolve()

    # Do incremental snapshot
    incremental_snapshot(
        project_root=project_root,
        file_paths=final_files,
        output_file=output_path,
        original_snapshot_func=generate_full_text,
        quiet=quiet
    )

    # Open in editor only on first run if skip_open_in_editor=False
    if not skip_open_in_editor:
        from .config import get_default_editor
        editor = get_default_editor()
        open_in_editor(str(output_path), editor, quiet=quiet)
        # refresh_textedit_in_background(str(output_path), quiet=quiet)  # Removed to avoid double reload on first run


def run_watch_mode(args):
    exts = args.extensions or get_default_extensions()
    exc_dirs = args.exclude_dirs or get_default_exclude_dirs()
    max_size = int(args.max_size * 1_000_000) if args.max_size > 0 else 0
    project_root = Path(args.directories[0]).resolve()
    output_path = Path(args.output).resolve()

    first_run = True

    def do_incremental():
        nonlocal first_run
        run_incremental_snapshot(
            directories=args.directories,
            files=args.files,
            output_file=output_path,
            extensions=exts,
            exclude_dirs=exc_dirs,
            max_size_mb=args.max_size,
            max_depth=args.max_depth,
            quiet=args.quiet,
            skip_open_in_editor=not first_run
        )

        # Always reload TextEdit when on macOS, even after first run
        if sys.platform == 'darwin':
            from .editor import refresh_textedit_in_background
            refresh_textedit_in_background(str(output_path), quiet=args.quiet)

        first_run = False

    def is_included_func(file_path: Path) -> bool:
        if file_path.resolve() == output_path.resolve():
            return False
        if file_path.suffix.lower() not in [e.lower() for e in exts]:
            return False
        rel_parts = file_path.relative_to(project_root).parts
        for part in rel_parts:
            for exc in exc_dirs:
                if Path(part).match(exc):
                    return False
        if max_size > 0 and file_path.stat().st_size > max_size:
            return False
        return True

    # Run initial snapshot
    do_incremental()
    # PASS files=args.files TO watch_directory
    watch_directory(
        project_root=project_root,
        snapshot_func=do_incremental,
        is_included_func=is_included_func,
        quiet=args.quiet,
        files=args.files
    )