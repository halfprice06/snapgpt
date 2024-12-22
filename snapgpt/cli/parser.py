import argparse

class CustomFormatter(argparse.HelpFormatter):
    def __init__(self, prog):
        super().__init__(prog, indent_increment=2, max_help_position=47, width=100)

    def _format_action(self, action):
        help_text = super()._format_action(action)
        if isinstance(action, argparse._SubParsersAction):
            help_text = '\n' + help_text
        return help_text

    def _format_usage(self, usage, actions, groups, prefix):
        if prefix is None:
            prefix = 'usage: '
        return super()._format_usage(usage, actions, groups, prefix)

    def _split_lines(self, text, width):
        if text.startswith('\n'):
            return [''] + super()._split_lines(text[1:], width)
        return super()._split_lines(text, width)


def build_argparser():
    parser = argparse.ArgumentParser(
        description='Create a snapshot of code files in specified directories, optimized for LLM context.',
        formatter_class=CustomFormatter,
        usage='%(prog)s [-h] [-d DIR [DIR ...]] [-f FILE [FILE ...]] [-o FILE]\n' +
              '         [-e EXT [EXT ...]] [--exclude-dirs DIR [DIR ...]] [--max-size MB]\n' +
              '         [--max-depth N] [-q] [--no-copy]\n' +
              '         [--set-default-editor EDITOR] [--set-default-extensions EXT [...]]\n' +
              '         [--set-default-exclude-dirs DIR [...]] [watch]'
    )

    # Base parser arguments
    parser.add_argument('-d', '--directories', nargs='+', default=["."],
                        metavar='DIR',
                        help='List of directories to scan')
    parser.add_argument('-f', '--files', nargs='+',
                        metavar='FILE',
                        help='List of specific files to include (overrides directory scanning)')
    parser.add_argument('-o', '--output', default="working_snapshot.md",
                        metavar='FILE',
                        help='Output file path')
    parser.add_argument('-e', '--extensions', nargs='+',
                        default=None,
                        metavar='EXT',
                        help='File extensions to include')
    parser.add_argument('--exclude-dirs', nargs='+', default=None,
                        metavar='DIR',
                        help='Directories to exclude from scanning')
    parser.add_argument('--max-size', type=float, default=0,
                        metavar='MB',
                        help='Maximum file size in MB (0 for no limit)')
    parser.add_argument('--max-depth', type=int, default=0,
                        metavar='N',
                        help='Maximum directory depth (0 for no limit)')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Suppress output')

    # Global settings
    parser.add_argument('--set-default-editor', 
                        choices=['cursor', 'code', 'windsurf', 'zed', 'xcode', 'textedit', 'notepad'],
                        metavar='EDITOR',
                        help='Set the default editor and exit')
    parser.add_argument('--set-default-extensions', nargs='+',
                        metavar='EXT',
                        help='Set the default file extensions and exit')
    parser.add_argument('--set-default-exclude-dirs', nargs='+',
                        metavar='DIR',
                        help='Set the default excluded dirs and exit')
    parser.add_argument('--no-copy', action='store_true',
                        help='Do not copy the snapshot to clipboard')

    # Subcommands
    subparsers = parser.add_subparsers(dest='subcommand', title='additional commands')

    watch_parser = subparsers.add_parser(
        'watch',
        help='Watch the directory for changes, auto-update snapshot.',
        description='Watch your codebase and automatically update the snapshot when files change.',
        formatter_class=CustomFormatter
    )
    watch_parser.add_argument('-d', '--directories', nargs='+', default=["."],
                              metavar='DIR',
                              help='List of directories to scan')
    # ADD THE -f / --files ARGUMENT HERE FOR WATCH:
    watch_parser.add_argument('-f', '--files', nargs='+',
                              default=None,
                              metavar='FILE',
                              help='List of specific files to include (overrides directory scanning)')

    watch_parser.add_argument('-o', '--output', default="working_snapshot.md",
                              metavar='FILE',
                              help='Output file path')
    watch_parser.add_argument('-e', '--extensions', nargs='+', default=None,
                              metavar='EXT',
                              help='File extensions to include')
    watch_parser.add_argument('--exclude-dirs', nargs='+', default=None,
                              metavar='DIR',
                              help='Directories to exclude')
    watch_parser.add_argument('--max-size', type=float, default=0,
                              metavar='MB',
                              help='Max file size in MB')
    watch_parser.add_argument('--max-depth', type=int, default=0,
                              metavar='N',
                              help='Max directory depth')
    watch_parser.add_argument('-q', '--quiet', action='store_true',
                              help='Suppress output')

    parser.add_argument('--markitdown-llm', action='store_true',
                        help='Enable LLM support for MarkItDown image descriptions')
    parser.add_argument('--markitdown-model', default='gpt-4o',
                        help='LLM model to use for MarkItDown image descriptions')

    return parser