from omcore.__about__ import ProjectBase
from omcore.__about__ import SetuptoolsBase
from omcore.__about__ import __version__


class Project(ProjectBase):
    name = 'omllm'
    description = 'omllm'

    dependencies = [
        f'omcore == {__version__}',
    ]

    optional_dependencies = {
        'omdev': [
            f'omdev == {__version__}',
        ],

        'interop': [
            'huggingface-hub ~= 1.24',

            'llama-cpp-python ~= 0.3',

            'mlx ~= 0.32; sys_platform == "darwin"',
            'mlx-lm ~= 0.31; sys_platform == "darwin"',

            'tinygrad ~= 0.13',

            'torch ~= 2.13',

            'transformers ~= 5.11',
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
