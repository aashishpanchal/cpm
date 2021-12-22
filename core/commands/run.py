import os
import json
from json import JSONDecodeError
import subprocess
from cpm.core.base import BaseCommand, CommandError
from cpm.core.color import colorize, style_error, style_success, style_warning, style_cpm
from cpm.utils.exceptions import (
    DirectoryNotFoundError,
    FileNotExitsError,
    AppNotFoundError,
    KeyWordNotFoundError,
    CompileError,
)
from cpm.utils.base import ExecutionTime


class Command(BaseCommand):
    help = "Run c++ {project}".format(
        project=colorize("project", fg="blue", opts=("bold",)))
    description = "Runs c++ project."
    source_file_suffixes = (".cpp",)
    lib_file_suffixes = (".a", ".o", ".so", ".dll")
    rewrite_template_suffixes = (
        ('.cpp', '.a'),
    )

    source = "source"

    executionTime_class = ExecutionTime()

    def add_arguments(self, parser):
        parser.add_argument('cpp_file_name', nargs='?',
                            help='Name of the c++ file.')
        parser.add_argument('--new-terminal', '--n-t', dest='new_terminal', action='store_true',
                            help='Open new terminal.')

    def handle(self, **options):
        cpp_file_name = options.pop("cpp_file_name")
        new_terminal = options.pop("new_terminal")
        if cpp_file_name is None:
            current_dir = os.getcwd()
            self.validate(current_dir)
            cpm_json = self.load_cpm_config(current_dir)
            try:
                cpp_file_name = cpm_json["entry_point"]
                self.validate_file_extension(cpp_file_name)
                self.validate(current_dir, cpp_file_name)
            except KeyError:
                raise CommandError("Entry point not found in cpm.json file")
        else:
            current_dir = os.path.join(os.getcwd())
            self.validate(current_dir, cpp_file_name)
            cpm_json = self.load_cpm_config(current_dir)

        apps = self.get_app(cpm_json)
        if apps is not None:
            lib_files = ""
            for app in apps:
                try:
                    self.validate_app(current_dir, app["name"])
                except KeyError:
                    raise KeyWordNotFoundError(style_error(
                        "App name not found in cpm.json file"))
                lib_dir = app.get("lib_dir", self.source)
                source_files = self._get_lib_files(
                    current_dir, app["name"], lib_dir)
                if len(source_files.items()) != 0:
                    self.stdout.write(
                        "[ %s ] --- %s" % (style_success("build"), style_warning(app["name"])), ending="")
                    lib_files += "".join(self._optimize_code_genrate(
                        current_dir, source_files)) + " "
            self.stdout.write("comebine complie %s" % style_cpm(cpp_file_name))
            self.run_now(cpp_file_name, lib_files, cpm_json.get('command'), new_terminal)
        else:
            self.run_now(cpp_file_name, "", "", new_terminal)

    def run_now(self, cpp_file_name, lib_files, commands, new_terminal=False):
        if commands is None:
            commands = ""

        exe_name = cpp_file_name.rpartition(".")[0] + ".exe"
        self.executionTime_class.start()
        cpp_complie_command = f"g++ -o {exe_name} {cpp_file_name} {lib_files} {commands}"
        complie_error = os.system(cpp_complie_command)
        self.executionTime_class.end()
        if complie_error != 0:
            raise CompileError(f"Error in compiling file {style_warning(cpp_file_name)}:\n{style_error(cpp_complie_command)}")
        else:
            self.stdout.write("complie successfully.", style_success,
                              ending=f" {self.executionTime_class.get_execution_time()}\n")
            if new_terminal:
                self.stdout.write("opening new terminal", style_warning)
                subprocess.run(
                    f"{exe_name}", creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                os.system(f"{exe_name}")

    def _get_lib_files(self, directory, app_name, lib_dir):
        if not os.path.exists(os.path.join(directory, app_name, lib_dir)):
            raise DirectoryNotFoundError("'%s' directory is not exist in '%s'" %
                                         (style_error(lib_dir),
                                          style_error(os.path.join(directory, app_name))))
        # make list of all source files
        source_files = {}
        for root, dirs, files in os.walk(os.path.join(directory, app_name, lib_dir)):
            for file in files:
                if file.endswith(self.source_file_suffixes):
                    source_files[str(os.path.join(root, file))] = app_name
        return source_files

    def _optimize_code_genrate(self, directory, source_files):
        """this function is used to optimize the code generation using g++

        Args:
            directory ([str]) : [current directory]
            source_files ([dict]) : [source files] 

        Raises:
            CompileError: [compile error]
        Returns:
            [list] : [optimized source files]
        """
        optimized_source_files = ""
        if not os.path.exists(os.path.join(directory, "build")):
            os.mkdir(os.path.join(directory, "build"))
        # get app_name and app_dir
        for source_file in source_files:
            for old_suffix, new_suffix in self.rewrite_template_suffixes:
                if source_file.endswith(old_suffix):
                    lib_file = source_file[:-len(old_suffix)] + new_suffix
                    break
            # check file is exist or not than compile it
            if not os.path.exists(os.path.join(directory, "build", source_files[source_file])):
                os.mkdir(os.path.join(directory, "build",
                         source_files[source_file]))
            # command = "g++ -c -o %s %s" % (lib_file, source_file)

            build_dir = os.path.join(
                directory, "build", source_files[source_file], os.path.basename(lib_file))

            self.executionTime_class.start()
            build = os.system(f"g++ -c {source_file} -o {build_dir}")
            self.executionTime_class.end()
            self.stdout.write(f" --- [ {style_warning(build_dir)} ]",
                              ending=f" {self.executionTime_class.get_execution_time()}\n")
            optimized_source_files += "".join(build_dir) + " "
            if build != 0:
                raise CompileError("Error in compiling file %s" %
                                   style_warning(source_file))
        return optimized_source_files

    def validate(self, directory, cpp_file=None):
        if cpp_file is None:
            if not os.path.exists(os.path.join(directory, "cpm.json")):
                raise FileNotExitsError("cpm.json file does not exist: %s" %
                                        style_error(directory))
        elif cpp_file is not None:
            if not os.path.exists(os.path.join(directory, cpp_file)):
                raise FileNotExitsError("%s this is not available inside directory: %s" %
                                        (style_error(cpp_file),
                                         style_error(directory)))

    def validate_file_extension(self, file_name):
        extension = file_name.rpartition(".")[2]
        if extension != "cpp":
            raise FileNotExitsError("%s is not a cpp file. please check %s file" % (
                style_error(file_name),
                style_error("cpm.json")
            ))

    def validate_app(self, directory, app_name):
        if not os.path.exists(os.path.join(directory, app_name)):
            raise AppNotFoundError("%s this is not available inside directory: %s" %
                                   (style_error(app_name),
                                    style_error(directory)))

    def get_app(self, cpm_json):
        try:
            return cpm_json["apps"]
        except KeyError:
            pass

    def load_cpm_config(self, directory):
        try:
            with open(os.path.join(directory, "cpm.json")) as cpm_config:
                return json.load(cpm_config)
        except FileNotFoundError:
            raise CommandError("cpm.json file does not exist: %s" %
                               style_error(directory))
        except JSONDecodeError as e:
            raise CommandError(
                f"cpm.json file is not valid json file:\nplease check {style_error(e)}")
