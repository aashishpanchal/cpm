
class CommandError(Exception):
    def __init__(self, *args, returncode=1, **kwargs):
        self.returncode = returncode
        super().__init__(*args, **kwargs)


class SystemCheckError(CommandError):
    pass


class CommandDoesNotExist(Exception):
    pass


class ImproperlyConfigured(Exception):
    pass


class DirectoryNotFoundError(CommandError):
    pass


class FileNotExitsError(CommandError):
    pass


class AppNotFoundError(CommandError):
    pass


class KeyWordNotFoundError(CommandError):
    pass


class CompileError(CommandError):
    pass
