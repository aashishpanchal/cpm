import sys

PY39 = sys.version_info >= (3, 9)
PY310 = sys.version_info >= (3, 10)


def get_version(version=None):
    version = get_complete_version(version)

    main = get_main_version(version)

    sub = ''
    if version[3] == 'alpha' and version[4] == 0:
        sub = '.dev'

    elif version[3] != 'final':
        mapping = {'alpha': 'a', 'beta': 'b'}
        sub = mapping[version[3]] + str(version[4])

    return main + sub


def get_main_version(version=None):
    version = get_complete_version(version)
    parts = 2 if version[2] == 0 else 3
    return '.'.join(str(x) for x in version[:parts])


def get_complete_version(version=None):
    """
    Return a tuple of the cpm version. If version argument is non-empty,
    check for correctness of the tuple provided.
    """
    if version is None:
        from cpm import VERSION as version
    else:
        assert len(version) == 5
        assert version[3] in ('alpha', 'beta', 'final')

    return version
