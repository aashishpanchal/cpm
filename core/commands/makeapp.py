from cpm.core.template import TemplateCommand
from cpm.core.color import style_error
from cpm.core.color import colorize

class Command(TemplateCommand):
    help = "Creates a cpm.json file in the current directory. "\
        "you can manage c++ {project}".format(
            project=colorize("app", fg="blue", opts=("bold",)))
    missing_args_message = style_error("You must provide an application name.")
    description = "Creates a c++ app."
    def add_arguments(self, parser):
        parser.add_argument('name', help='Name of the application.')
        parser.add_argument('directory', nargs='?',
                            help='Optional destination directory')
        parser.add_argument(
            '--directory', '-d', dest='directory',
            help='Optional destination directory'
        )
        parser.add_argument(
            '--name', '-n', dest='name',
            action='store_true',
            help='The project name.'
        )

    def handle(self, **options):
        app_name = options.pop('name')
        target = options.pop('directory')
        super().handle('app', app_name, target, **options)
