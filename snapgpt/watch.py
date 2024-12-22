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
    def __init__(self, project_root: Path, snapshot_func, is_included_func, quiet=False):
        super().__init__()
        self.project_root = project_root
        self.snapshot_func = snapshot_func  # Function that does incremental snapshot
        self.is_included_func = is_included_func  # Checks if a file is relevant for snapshot
        self.quiet = quiet
        self.debounce_timers = {}
        self.debounce_seconds = 1.0  # short delay to avoid repeated triggers if a file is changing rapidly

    def on_modified(self, event):
        """Called when a file is modified."""
        if event.is_directory:
            return
        file_path = Path(event.src_path).resolve()

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


def watch_directory(project_root: Path, snapshot_func, is_included_func, quiet=False):
    """
    Set up the Watchdog observer to watch the entire project root for changes.
    snapshot_func() is a callback that regenerates the snapshot.
    is_included_func() checks if a file belongs in the snapshot or not.
    """
    event_handler = SnapGPTEventHandler(project_root, snapshot_func, is_included_func, quiet=quiet)
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