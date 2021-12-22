import pkgutil
import os
import sys
import cpm
from collections import defaultdict
from argparse import (
    _AppendConstAction, _CountAction, _StoreConstAction, _SubParsersAction,
)
from importlib import import_module
from difflib import get_close_matches
from cpm.core.base import (
    BaseCommand, CommandParser, CommandError,
)
from cpm.utils.exceptions import ImproperlyConfigured


def find_commands(core_dir):
    """
    Given a path to a management directory, return a list of all the command file
    names that are available.
    """
    command_dir = os.path.join(core_dir, 'commands')
    return [name for _, name, is_pkg in pkgutil.iter_modules([command_dir])
            if not is_pkg and not name.startswith('_')]


def load_command_class(app_name, name):
    module = import_module('%s.commands.%s' % (app_name, name))
    return module.Command()


def get_commands():
    commands = {name: 'cpm.core' for name in find_commands(__path__[0])}
    other_commands = os.path.join(os.getcwd(), 'extra_commands')
    if os.path.exists(os.path.join(other_commands, 'commands')):
        commands.update({name: 'extra_commands' for name in find_commands(other_commands)})
        pass
    return commands


def call_command(command_name, *args, **options):
    """
    Call the given command, with the given options and args/kwargs.

    This is the primary API you should use for calling specific commands.

    `command_name` may be a string or a command object. Using a string is
    preferred unless the command object is required for further processing or
    testing.

    Some examples:
        call_command('init')
        call_command('run', plain=True)

        from cpm.core.commands import init
        cmd = init.Command()
        call_command(cmd, verbosity=0, interactive=False)
        # Do something with cmd ...
    """
    if isinstance(command_name, BaseCommand):
        # Command object passed in.
        command = command_name
        command_name = command.__class__.__module__.split('.')[-1]
    else:
        # Load the command object by name.
        try:
            app_name = get_commands()[command_name]
        except KeyError:
            raise CommandError("Unknown command: %r" % command_name)

        if isinstance(app_name, BaseCommand):
            # If the command is already loaded, use it directly.
            command = app_name
        else:
            command = load_command_class(app_name, command_name)

    # Simulate argument parsing to get the option defaults (see #10080 for details).
    parser = command.create_parser('', command_name)
    # Use the `dest` option name from the parser option
    opt_mapping = {
        min(s_opt.option_strings).lstrip('-').replace('-', '_'): s_opt.dest
        for s_opt in parser._actions if s_opt.option_strings
    }
    arg_options = {opt_mapping.get(
        key, key): value for key, value in options.items()}
    parse_args = []
    for arg in args:
        if isinstance(arg, (list, tuple)):
            parse_args += map(str, arg)
        else:
            parse_args.append(str(arg))

    def get_actions(parser):
        # Parser actions and actions from sub-parser choices.
        for opt in parser._actions:
            if isinstance(opt, _SubParsersAction):
                for sub_opt in opt.choices.values():
                    yield from get_actions(sub_opt)
            else:
                yield opt

    parser_actions = list(get_actions(parser))
    mutually_exclusive_required_options = {
        opt
        for group in parser._mutually_exclusive_groups
        for opt in group._group_actions if group.required
    }
    # Any required arguments which are passed in via **options must be passed
    # to parse_args().
    for opt in parser_actions:
        if (
            opt.dest in options and
            (opt.required or opt in mutually_exclusive_required_options)
        ):
            parse_args.append(min(opt.option_strings))
            if isinstance(opt, (_AppendConstAction, _CountAction, _StoreConstAction)):
                continue
            value = arg_options[opt.dest]
            if isinstance(value, (list, tuple)):
                parse_args += map(str, value)
            else:
                parse_args.append(str(value))
    defaults = parser.parse_args(args=parse_args)
    defaults = dict(defaults._get_kwargs(), **arg_options)
    # Raise an error if any unknown options were passed.
    stealth_options = set(command.base_stealth_options +
                          command.stealth_options)
    dest_parameters = {action.dest for action in parser_actions}
    valid_options = (dest_parameters | stealth_options).union(opt_mapping)
    unknown_options = set(options) - valid_options
    if unknown_options:
        raise TypeError(
            "Unknown option(s) for %s command: %s. "
            "Valid options are: %s." % (
                command_name,
                ', '.join(sorted(unknown_options)),
                ', '.join(sorted(valid_options)),
            )
        )
    # Move positional args out of options to mimic legacy optparse
    args = defaults.pop('args', ())
    if 'skip_checks' not in options:
        defaults['skip_checks'] = True

    return command.execute(*args, **defaults)


class ManagementUtility:
    """
    Encapsulate the logic of the cpm utilities.
    """

    def __init__(self, argv=None):
        self.argv = argv or sys.argv[:]  # return list of strings argument
        self.prog_name = os.path.basename(
            self.argv[0])  # return the program name
        if self.prog_name == '__main__.py':
            self.prog_name = 'python -m cpm'
        self.settings_exception = None

    def main_help_text(self, commands_only=False):
        """Return the script's main help text, as a string."""
        if commands_only:
            usage = sorted(get_commands())
        else:  # show all commands available in cpm
            usage = [
                "",
                "Type '%s help <subcommand>' for help on a specific subcommand." % self.prog_name,
                "",
                "Available subcommands:",
                "",
                "Commands:",
            ]
            commands_dict = defaultdict(lambda: [])
            for name in get_commands().keys():
                commands_dict['cpm'].append(name)

            for name in sorted(commands_dict['cpm']):
                usage.append(
                    f"   {name:24}{self.fetch_command(name).description}")

        return '\n'.join(usage)

    def fetch_command(self, subcommand):
        """
        Try to fetch the given subcommand, printing a message with the
        appropriate command called from the command line (usually
        "cpm" or "cpm.py") if it can't be found.
        """
        # Get commands outside of try block to prevent swallowing exceptions
        commands = get_commands()
        try:
            app_name = commands[subcommand]
        except KeyError:
            # return a list of the most similar names
            possible_matches = get_close_matches(subcommand, commands)
            sys.stderr.write('Unknown command: %r' % subcommand)
            if possible_matches:
                sys.stderr.write('. Did you mean %s?' % possible_matches[0])
            sys.stderr.write("\nType '%s help' for usage.\n" % self.prog_name)
            sys.exit(1)  # exit now

        if isinstance(app_name, BaseCommand):
            # If the command is already loaded, use it directly.
            klass = app_name
        else:
            klass = load_command_class(app_name, subcommand)
        return klass

    def execute(self):
        """
        Given the command-line arguments, figure out which subcommand is being
        run, create a parser appropriate to that command, and run it.
        """
        # self.argv[1] is containe the subcommand argument: like 'cpm start, cpm help' and show on
        try:
            subcommand = self.argv[1]
        except IndexError:
            # subcommand not given on the command line. os set default subcommand to 'help'
            subcommand = 'help'  # Display help if no arguments were given.

        # Preprocess options to extract --settings and --pythonpath.
        # These options could affect the commands that are available, so they
        # must be processed early.
        parser = CommandParser(
            description="cpm command line utility",
            prog=self.prog_name,
            usage='%(prog)s subcommand [options] [args]',
            add_help=False,
            allow_abbrev=False,
        )
        # parser.add_argument('--settings')
        # parser.add_argument('--pythonpath')
        parser.add_argument('args', nargs='*')  # catch-all
        try:
            options, args = parser.parse_known_args(self.argv[2:])
            # options is a Namespace object, is containe args of after subcommand
        except CommandError:
            pass  # Ignore any option errors at this point.

        if subcommand == 'help':
            if '--commands' in args:
                sys.stdout.write(self.main_help_text(
                    commands_only=True) + '\n')
            elif not options.args:
                sys.stdout.write(self.main_help_text() + '\n')
            else:
                self.fetch_command(options.args[0]).print_help(
                    self.prog_name, options.args[0])

        elif subcommand == 'version' or self.argv[1:] in (['--version'], ['-v']):
            sys.stdout.write(cpm.get_version() + '\n')
        elif self.argv[1:] in (['--help'], ['-h']):
            sys.stdout.write(self.main_help_text() + '\n')
        else:
            self.fetch_command(subcommand).run_from_argv(self.argv)


def execute_from_command_line(argv=None):
    """Run a ManagementUtility."""
    utility = ManagementUtility(argv)
    utility.execute()
