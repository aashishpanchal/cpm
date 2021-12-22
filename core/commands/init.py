import sys
import os
import json
from cpm.utils.exceptions import CommandError
from cpm.core.template import TemplateCommand
from cpm.utils import cpm_ascii
from cpm.core.color import style_error, style_cpm, colorize, style_warning, style_success


class Command(TemplateCommand):
    help = "Creates a cpm.json file in the current directory. "\
        "you can manage c++ {project}".format(
            project=colorize("project", fg="blue", opts=("bold",)))
    missing_args_message = style_error("You must provide a project name.")
    description = "Creates a c++ project."
    default_project_version = "1.0.0"
    # init_input = { value: (message, default_value) }
    init_input = {
        "author": ("project author", ""),
        "description": ("project description", ""),
        "entry_point": ("project entry point" + style_warning("(main.cpp)"), "main.cpp"),
    }

    def add_arguments(self, parser):
        parser.add_argument('name', help='Name of the application or project.',
                            type=str)
        parser.add_argument('directory', nargs='?',
                            help='Optional destination directory')
        parser.add_argument('project-version', nargs="?",
                            default=self.default_project_version,
                            help='Version of the application or project.',)
        parser.add_argument(
            '--project-version', '-p-v', dest='project-version',
            help='The project version.'
        )
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
        super().handle('project', app_name, target, **options)

    def handle_level(self, name, target, **options):
        init_data = {"name": name, "version": options.pop("project-version")}
        try:
            for field in self.init_input:
                if field == "entry_point":
                    while True:
                        value = self.get_input_data(
                            message=self.init_input[field][0], default=self.init_input[field][1])
                        try:
                            self._validate_enter_name(value)
                            init_data[field] = value
                            break
                        except Exception as e:
                            self.stdout.write(str(e), style_error)
                            continue
                else:
                    init_data[field] = self.get_input_data(
                        message=self.init_input[field][0], default=self.init_input[field][1])
        except KeyboardInterrupt:
            self.stderr.write('\nOperation cancelled.', style_error)
            sys.exit(1)
        except Exception as e:
            self.stderr.write(
                '\Some Probles to create your project.', style_error)
            sys.exit(1)

        return init_data

    def _cpm_logo(self):
        self.stdout.write(cpm_ascii(), style_cpm)

    def get_input_data(self, message, default=None):
        raw_value = input(message + ": ")
        if default and raw_value == '':
            raw_value = default
        return raw_value

    def _validate_enter_name(self, name):
        if name.rpartition('.')[2].lower() != 'cpp':
            raise CommandError("The name must end with '.cpp'.")

    def execute(self, *args, **options):
        self._cpm_logo()
        self.handle(**options)
