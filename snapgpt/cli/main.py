import sys
import warnings
from warnings import simplefilter
simplefilter("ignore", ResourceWarning)

from .parser import build_argparser
from .config import (
    do_first_time_setup, set_default_editor, set_default_extensions,
    set_default_exclude_dirs, get_config, save_config
)
from .commands import run_incremental_snapshot, run_watch_mode

def main():
    # First-time setup if needed
    do_first_time_setup()

    parser = build_argparser()
    args = parser.parse_args()

    # Handle global commands first
    if args.set_default_editor:
        success = set_default_editor(args.set_default_editor, quiet=False)
        sys.exit(0 if success else 1)

    if args.set_default_extensions:
        success = set_default_extensions(args.set_default_extensions, quiet=False)
        sys.exit(0 if success else 1)

    if args.set_default_exclude_dirs:
        success = set_default_exclude_dirs(args.set_default_exclude_dirs, quiet=False)
        sys.exit(0 if success else 1)

    # Possibly disable auto_copy for the run
    if args.no_copy:
        config = get_config()
        config['auto_copy_to_clipboard'] = False
        save_config(config)

    if not args.subcommand:
        # run incremental snapshot once
        run_incremental_snapshot(
            directories=args.directories,
            files=args.files,
            output_file=args.output,
            extensions=args.extensions,
            exclude_dirs=args.exclude_dirs,
            max_size_mb=args.max_size,
            max_depth=args.max_depth,
            quiet=args.quiet
        )
        sys.exit(0)

    if args.subcommand == 'incremental':
        run_incremental_snapshot(
            directories=args.directories,
            files=args.files,
            output_file=args.output,
            extensions=args.extensions,
            exclude_dirs=args.exclude_dirs,
            max_size_mb=args.max_size,
            max_depth=args.max_depth,
            quiet=args.quiet
        )
        sys.exit(0)

    elif args.subcommand == 'watch':
        run_watch_mode(args)