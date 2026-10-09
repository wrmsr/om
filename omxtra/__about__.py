from omcore.__about__ import ProjectBase
from omcore.__about__ import SetuptoolsBase
from omcore.__about__ import __version__


class Project(ProjectBase):
    name = 'omxtra'
    description = 'omxtra'

    dependencies = [
        f'omcore == {__version__}',
    ]

    optional_dependencies: dict = {
        'omdev': [
            f'omdev == {__version__}',
        ],

        'ominfra': [
            f'ominfra == {__version__}',
        ],

        'ssh': [
            'asyncssh ~= 2.24',  # cffi

            'paramiko ~= 5.0',  # !! LGPL
        ],

        'wiki': [
            'mwparserfromhell ~= 0.7',

            'wikitextparser ~= 3.0',  # !! GPL
        ],

        'zmq': [
            'pyzmq ~= 27.2',
        ],
    }

    entry_points = {
        'omcore.manifests': {name: name},
    }


class Setuptools(SetuptoolsBase):
    find_packages = {
        'include': [Project.name, f'{Project.name}.*'],
        'exclude': [*SetuptoolsBase.find_packages['exclude']],
    }
