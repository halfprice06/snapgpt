import time
import threading
from pathlib import Path
import sys

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("Please install watchdog (e.g. `pip install watchdog`) to use the watch feature.")
    sys.exit(1)

from .incremental import load_index, compute_file_hash, save_index

class SnapGPTEventHandler(FileSystemEventHandler):
    def __init__(self, project_root: Path, snapshot_func, is_included_func, quiet=False, files=None):
        super().__init__()
        self.project_root = project_root
        self.snapshot_func = snapshot_func  # Function that does incremental snapshot
        self.is_included_func = is_included_func  # Checks if a file is relevant for snapshot
        self.quiet = quiet
        self.files = [Path(f).resolve() for f in files] if files else None
        self.debounce_timers = {}
        self.debounce_seconds = 1.0  # short delay to avoid repeated triggers if a file is changing rapidly

    def on_modified(self, event):
        """Called when a file is modified."""
        if event.is_directory:
            return
        file_path = Path(event.src_path).resolve()

        # If specific files were provided, only watch those
        if self.files is not None and file_path not in self.files:
            return

        # If the file isn't included, do nothing
        if not self.is_included_func(file_path):
            return

        # Debounce: cancel existing timer if any, start a new one
        if file_path in self.debounce_timers:
            self.debounce_timers[file_path].cancel()

        timer = threading.Timer(self.debounce_seconds, self.handle_file_change, args=[file_path])
        timer.start()
        self.debounce_timers[file_path] = timer

    def on_created(self, event):
        """Called when a file is created."""
        if event.is_directory:
            return
        self.on_modified(event)  # same logic for newly created files

    def on_deleted(self, event):
        """Called when a file is deleted."""
        if event.is_directory:
            return
        file_path = Path(event.src_path).resolve()

        # If specific files were provided, only watch those
        if self.files is not None and file_path not in self.files:
            return

        # If the file was tracked, let's also re-run the snapshot
        # so working_snapshot.md will remove references to that file.
        if self.is_included_func(file_path):
            # Debounce just like we do on modified
            if file_path in self.debounce_timers:
                self.debounce_timers[file_path].cancel()

            timer = threading.Timer(self.debounce_seconds, self.handle_file_change, args=[file_path])
            timer.start()
            self.debounce_timers[file_path] = timer

    def on_moved(self, event):
        """Called when a file is moved/renamed."""
        if event.is_directory:
            return
        # A move event has event.src_path and event.dest_path
        old_file_path = Path(event.src_path).resolve()
        new_file_path = Path(event.dest_path).resolve()

        # If specific files were provided, only watch those
        if self.files is not None:
            if old_file_path not in self.files and new_file_path not in self.files:
                return

        # If the old path was tracked or the new path is relevant,
        # let's refresh the snapshot in either case.

        # Cancel any existing timers for the old path
        if old_file_path in self.debounce_timers:
            self.debounce_timers[old_file_path].cancel()

        # Trigger snapshot for the old path, in case we need to remove it
        if self.is_included_func(old_file_path):
            timer_old = threading.Timer(self.debounce_seconds, self.handle_file_change, args=[old_file_path])
            timer_old.start()
            self.debounce_timers[old_file_path] = timer_old

        # Also trigger for the new path, if included
        if self.is_included_func(new_file_path):
            timer_new = threading.Timer(self.debounce_seconds, self.handle_file_change, args=[new_file_path])
            timer_new.start()
            self.debounce_timers[new_file_path] = timer_new

    def handle_file_change(self, file_path: Path):
        """
        After the debounce delay, actually process the file change:
          1. Re-run the incremental snapshot function
        """
        try:
            if not self.quiet:
                print(f"[watch] Detected change in: {file_path}")
            self.snapshot_func()
        except Exception as e:
            print(f"Error while updating snapshot: {e}", file=sys.stderr)


def watch_directory(project_root: Path, snapshot_func, is_included_func, quiet=False, files=None):
    """
    Set up the Watchdog observer to watch the entire project root for changes.
    snapshot_func() is a callback that regenerates the snapshot.
    is_included_func() checks if a file belongs in the snapshot or not.
    files is an optional list of specific files to watch.
    """
    event_handler = SnapGPTEventHandler(project_root, snapshot_func, is_included_func, quiet=quiet, files=files)
    observer = Observer()
    observer.schedule(event_handler, str(project_root), recursive=True)
    observer.start()
    if not quiet:
        print("[watch] Now watching for file changes. Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        if not quiet:
            print("[watch] Stopping...")
        observer.stop()
    observer.join()

    