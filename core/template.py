import os
import json
import cpm
import sys
import shutil
from cpm.core.base import BaseCommand
from cpm.core.color import style_error, style_success, style_warning
from cpm.utils.exceptions import CommandError

class TemplateCommand(BaseCommand):
    help = ""
    rewrite_template_suffixes = (
        ('.cpp-tpl', '.cpp'),
        ('.hpp-tpl', '.hpp'),
        ('.h-tpl', '.h'),
    )

    def add_arguments(self, parser):
        parser.add_argument('name', help='Name of the application or project.')
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

    def handle_level(self, name: str, target: str, **options) -> dict:
        pass

    def handle(self, app_or_project, name, target=None, **options):
        self.app_or_project = app_or_project
        self.a_or_an = 'an' if app_or_project == 'app' else 'a'
        self.validate_name(name)

        if target is None:
            top_dir = os.path.join(os.getcwd(), name)
            try:
                os.makedirs(top_dir)
            except FileExistsError:
                raise CommandError("'%s' already exists" %
                                   style_error(top_dir))
            except OSError as e:
                raise CommandError(e)
        else:
            if app_or_project == "project":
                top_dir = os.path.abspath(os.path.expanduser(target))
                self.validate_project(top_dir)
            else:
                dir_ = os.path.abspath(os.path.expanduser(target))
                top_dir = os.path.join(dir_, name)
                try:
                    os.makedirs(top_dir)
                except FileExistsError:
                    raise CommandError("'%s' already exists" %
                                       style_error(top_dir))
                except OSError as e:
                    raise CommandError(e)
            if app_or_project == 'app':
                self.validate_name(os.path.basename(top_dir), 'directory')
            if not os.path.exists(top_dir):
                raise CommandError("Destination directory '%s' does not "
                                   "exist, please create it first." % style_error(top_dir))

        dic = self.handle_level(name, target, **options)
        if dic is not None:
            dic_str = json.dumps(dic, indent=4)
            with open(os.path.join(top_dir, 'cpm.json'), 'w') as f:
                f.write(dic_str)

        base_name = '%s_name' % app_or_project
        base_subdir = '%s_template' % app_or_project
        base_directory = '%s_directory' % app_or_project
        camel_case_value = ''.join(x for x in name.title() if x != '_')

        template_dir = self.handle_template(base_subdir)
        prefix_length = len(template_dir) + 1

        # search template files
        for root, dirs, files in os.walk(template_dir):
            path_rest = root[prefix_length:]
            relative_dir = path_rest.replace(
                base_name, name)  # include, lib, etc
            if relative_dir:
                target_dir = os.path.join(top_dir, relative_dir)
                os.makedirs(target_dir, exist_ok=True)
            for filename in files:
                old_path = os.path.join(root, filename)
                if dic is not None and app_or_project == "project":
                    new_path = os.path.join(
                        top_dir, relative_dir, filename.replace(
                            'entry_point', dic['entry_point'].rpartition(".")[0])
                    )
                else:
                    new_path = os.path.join(
                        top_dir, relative_dir, filename.replace(
                            base_name, name)
                    )
                for old_suffix, new_suffix in self.rewrite_template_suffixes:
                    if new_path.endswith(old_suffix):
                        new_path = new_path[:-len(old_suffix)] + new_suffix
                        break  # Only rewrite once

                if os.path.exists(new_path):
                    raise CommandError(
                        "%s already exists. Overlaying %s %s into an existing "
                        "directory won't replace conflicting files." % (
                            style_error(new_path), style_error(
                                self.a_or_an), style_error(app_or_project),
                        )
                    )
                # copy file to new path and replace it with new path name and new name of file in template directory.
                shutil.copyfile(old_path, new_path)
                try:
                    # copy permission bits (mode)
                    shutil.copymode(old_path, new_path)
                    self.make_writeable(new_path)
                except OSError:
                    self.stderr.write(
                        "Notice: Couldn't set permission bits on %s. You're "
                        "probably using an uncommon filesystem setup. No "
                        "problem." % new_path)
        self.stdout.write("%s create your %s" % (
            style_success("successfully"),
            style_warning(f"{name} {app_or_project}"),
        ))

    def handle_template(self, subdir):
        return os.path.join(cpm.__path__[0], 'conf', subdir)

    def validate_project(self, project_dir):
        if os.path.exists(os.path.join(project_dir, 'cpm.json')):
            raise CommandError(
                "%s already exists. Can't create a new project in an existing "
                "directory." % style_error(project_dir))

    def validate_name(self, name, name_or_dir='name'):
        if name is None:
            raise CommandError('you must provide {an} {app} name'.format(
                an=style_error(self.a_or_an),
                app=style_error(self.app_or_project),
            ))
        # Check it's a valid directory name.
        if not name.isidentifier():
            raise CommandError(
                "'{name}' is not a valid {app} {type}. Please make sure the {type} is a valid identifier.".format(
                    name=style_error(name),
                    app=style_error(self.app_or_project),
                    type=style_error(name_or_dir),
                )
            )

    def make_writeable(self, filename):
        """
        Make sure that the file is writeable.
        Useful if our source is read-only.
        """
        if not os.access(filename, os.W_OK):
            st = os.stat(filename)
            new_permissions = stat.S_IMODE(st.st_mode) | stat.S_IWUSR
            os.chmod(filename, new_permissions)
