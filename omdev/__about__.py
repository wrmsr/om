from omcore.__about__ import ProjectBase
from omcore.__about__ import SetuptoolsBase
from omcore.__about__ import __version__


class Project(ProjectBase):
    name = 'omdev'
    description = 'omdev'

    dependencies = [
        f'omcore == {__version__}',
    ]

    optional_dependencies = {
        'ominfra': [
            f'ominfra == {__version__}',
        ],

        'omllm': [
            f'omllm == {__version__}',
        ],

        #

        'black': [
            'black ~= 26.5',
        ],

        'c': [
            'pycparser ~= 3.0',

            'pcpp ~= 1.30',
        ],

        'doc': [
            'docutils ~= 0.23',
        ],

        'mypy': [
            'mypy ~= 2.3',
        ],

        'ocr': [
            'pytesseract ~= 0.3',

            'rapidocr-onnxruntime ~= 1.4',
        ],

        'pillow': [
            'pillow ~= 12.3',
        ],

        'prof': [
            'gprof2dot ~= 2025.4',
        ],

        'pyright': [
            'basedpyright ~= 1.39',
        ],

        'qr': [
            'segno ~= 1.6',
        ],

        'ruff': [
            'ruff ~= 0.16',
        ],

        # 'sqlrepl': [
        #     'litecli ~= 1.17',
        #     'mycli ~= 2.17',
        #     'pgcli ~= 4.6',
        # ],

        'tui-syntax': [
            'tree-sitter ~= 0.26',
            'tree-sitter-bash ~= 0.25',
            'tree-sitter-css ~= 0.25',
            'tree-sitter-go ~= 0.25',
            'tree-sitter-html ~= 0.23',
            'tree-sitter-java ~= 0.23',
            'tree-sitter-javascript ~= 0.25',
            'tree-sitter-json ~= 0.24',
            'tree-sitter-markdown ~= 0.5',
            'tree-sitter-python ~= 0.25',
            'tree-sitter-regex ~= 0.25',
            'tree-sitter-rust ~= 0.24',
            'tree-sitter-sql ~= 0.3',
            'tree-sitter-toml ~= 0.7',
            'tree-sitter-xml ~= 0.7',
            'tree-sitter-yaml ~= 0.7',
        ],
    }

    entry_points = {
        'omcore.manifests': {name: name},
    }

    cli_scripts = {
        'om': f'{name}.cli.main:_main',
    }


class Setuptools(SetuptoolsBase):
    cext = True
    rs = True

    find_packages = {
        'include': [Project.name, f'{Project.name}.*'],
        'exclude': [*SetuptoolsBase.find_packages['exclude']],
    }
