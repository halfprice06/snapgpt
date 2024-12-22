import os
import hashlib
import json
from pathlib import Path
import sys

INDEX_FILENAME = ".snapgpt_index"


def compute_file_hash(file_path: Path) -> str:
    """Compute a hash for the given file to detect changes."""
    hasher = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
    except (IOError, OSError):
        return ""  # Return empty if unreadable
    return hasher.hexdigest()


def load_index(project_root: Path) -> dict:
    """Load the .snapgpt_index file if it exists, else return a blank structure."""
    index_path = project_root / INDEX_FILENAME
    if index_path.exists():
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"files": {}}


def save_index(project_root: Path, index_data: dict):
    """Save the index data back to .snapgpt_index in the project root."""
    index_path = project_root / INDEX_FILENAME
    try:
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2)
    except IOError as e:
        print(f"Failed to save .snapgpt_index: {e}", file=sys.stderr)


def incremental_snapshot(
    project_root: Path,
    file_paths,
    output_file: Path,
    original_snapshot_func,
    quiet=False
) -> None:
    """
    Create or update a code snapshot incrementally by leveraging the .snapgpt_index file.
    
    :param project_root: The root directory of the project.
    :param file_paths: List of Path objects to include in the snapshot (already filtered by extension/size).
    :param output_file: The path to write the final combined snapshot (working_snapshot.md).
    :param original_snapshot_func: The existing function that generates the final file contents
                                   (we'll override reading from disk for unchanged files).
    :param quiet: Suppress progress messages if True.
    """
    index_data = load_index(project_root)

    changed_or_new_files = []
    unchanged_files = []
    for fp in file_paths:
        current_hash = compute_file_hash(fp)
        old_record = index_data["files"].get(str(fp), {})
        if not old_record or old_record.get("hash") != current_hash:
            changed_or_new_files.append(fp)
        else:
            unchanged_files.append(fp)

    if not quiet:
        print(f"Files changed/new: {len(changed_or_new_files)}, Unchanged: {len(unchanged_files)}")

    # Option A: We are doing a *full rewrite* of the output file but skip reading disk for unchanged files.
    # We still need the file text for unchanged files. Two approaches:
    #   1) Reread from disk anyway (but then we gain no big speed advantage).
    #   2) Store the actual file text in the index (makes a huge index).
    # We'll do #1 for simplicity: we do a full rewrite each time, but the incremental step is that
    # we only re-hash changed files next time.

    snapshot_text = original_snapshot_func(file_paths)
    with open(output_file, 'w', encoding='utf-8') as out_f:
        out_f.write(snapshot_text)

    # Update the index with new/changed files
    for fp in changed_or_new_files:
        new_hash = compute_file_hash(fp)
        index_data["files"][str(fp)] = {"hash": new_hash}

    # Remove files from the index that no longer exist
    existing_paths = {str(fp) for fp in file_paths}
    removed_files = []
    for stored_path in list(index_data["files"].keys()):
        if stored_path not in existing_paths:
            removed_files.append(stored_path)
            del index_data["files"][stored_path]

    save_index(project_root, index_data)

    if not quiet and removed_files:
        print(f"Removed from index (deleted/renamed): {removed_files}")