import os
import sys
import argparse
from argparse import ArgumentParser, HelpFormatter
from io import TextIOBase
from cpm.utils.exceptions import ImproperlyConfigured, CommandError, SystemCheckError
from cpm import __version__


class CommandParser(ArgumentParser):
    def __init__(self, *, missing_args_message=None, called_from_command_line=None, **kwargs):
        self.missing_args_message = missing_args_message
        self.called_from_command_line = called_from_command_line
        super().__init__(**kwargs)

    def parse_args(self, args=None, namespace=None):
        # Catch missing argument for a better error message
        if (self.missing_args_message and
                not (args or any(not arg.startswith('-') for arg in args))):
            self.error(self.missing_args_message)
        return super().parse_args(args, namespace)

    def error(self, message):
        if self.called_from_command_line:
            super().error(message)
        else:
            raise CommandError("Error: %s" % message)


class CpmHelpFormatter(HelpFormatter):
    """
    Customized formatter so that command-specific arguments appear in the
    --help output before arguments common to all commands.
    """
    show_last = {
        '--version', '--help', '--traceback'
    }

    def _reordered_actions(self, actions):
        return sorted(
            actions,
            key=lambda a: set(a.option_strings) & self.show_last != set()
        )

    def add_usage(self, usage, actions, *args, **kwargs):
        super().add_usage(usage, self._reordered_actions(actions), *args, **kwargs)

    def add_arguments(self, actions):
        super().add_arguments(self._reordered_actions(actions))


class OutputWrapper(TextIOBase):
    """
    Wrapper around stdout/stderr
    """
    @property
    def style_func(self):
        return self._style_func

    @style_func.setter
    def style_func(self, style_func):
        if style_func and self.isatty():
            self._style_func = style_func
        else:
            self._style_func = lambda x: x

    def __init__(self, out, ending='\n'):
        self._out = out
        self.style_func = None
        self.ending = ending

    def __getattr__(self, name):
        return getattr(self._out, name)

    def flush(self):
        if hasattr(self._out, 'flush'):
            self._out.flush()

    def isatty(self):
        return hasattr(self._out, 'isatty') and self._out.isatty()

    def write(self, msg='', style_func=None, ending=None):
        ending = self.ending if ending is None else ending
        if ending and not msg.endswith(ending):
            msg += ending
        style_func = style_func or self.style_func
        self._out.write(style_func(msg))


class BaseCommand:
    help = ''
    description = ''
    stealth_options = ()
    suppressed_base_arguments = set()

    def __init__(self, stdout=None, stderr=None):
        self.stdout = OutputWrapper(stdout or sys.stdout)
        self.stderr = OutputWrapper(stderr or sys.stderr)

    def get_version(self):
        return __version__

    def add_base_argument(self, parser, *args, **kwargs):
        for arg in args:
            if arg in self.suppressed_base_arguments:
                kwargs['help'] = argparse.SUPPRESS
                break
        parser.add_argument(*args, **kwargs)

    def add_arguments(self, parser):
        pass

    def create_parser(self, prog_name, subcommand, **kwargs):
        parser = CommandParser(
            prog='%s %s' % (os.path.basename(prog_name), subcommand),
            description=self.help or None,
            formatter_class=CpmHelpFormatter,
            missing_args_message=getattr(self, 'missing_args_message', None),
            called_from_command_line=getattr(
                self, '_called_from_command_line', None),
            **kwargs
        )
        self.add_base_argument(
            parser, '-v', '--version', action='version', version=self.get_version(),
            help="Show program's version number and exit.",
        )
        self.add_base_argument(
            parser, '--traceback', action='store_true',
            help='Raise on CommandError exceptions.',
        )
        self.add_arguments(parser)
        return parser

    def print_help(self, prog_name, subcommand):
        parser = self.create_parser(prog_name, subcommand)
        parser.print_help()

    def run_from_argv(self, argv):
        self._called_from_command_line = True
        parser = self.create_parser(argv[0], argv[1])

        options = parser.parse_args(argv[2:])
        cmd_options = vars(options)  # return { name: value}
        # Move positional args out of options to mimic legacy optparse
        args = cmd_options.pop('args', ())
        try:
            self.execute(*args, **cmd_options)
        except CommandError as e:
            if options.traceback:
                raise CommandError(e)

            # SystemCheckError takes care of its own formatting.
            if isinstance(e, SystemCheckError):
                self.stderr.write(str(e), lambda x: x)
            else:
                self.stderr.write('%s: %s' % (e.__class__.__name__, e))
            sys.exit(e.returncode)

    def execute(self, *args, **options):
        if options.get('stdout'):
            self.stdout = OutputWrapper(options['stdout'])
        if options.get('stderr'):
            self.stderr = OutputWrapper(options['stderr'])
        output = self.handle(*args, **options)
        return output

    def handle(self, *args, **options):
        """
        The actual logic of the command. Subclasses must implement
        this method.
        """
        raise NotImplementedError(
            'subclasses of BaseCommand must provide a handle() method')
