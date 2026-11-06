import os.path

from omcore.os.temp import temp_dir_context

from ..discovery import LiteSourceDiscovery
from ..discovery import LiteSourceTarget
from ..discovery import discover_lite_sources


##


def test_discover_lite_sources():
    with temp_dir_context() as src_dir:
        files = {
            'root/__init__.py': "raise RuntimeError('must not import during discovery')\n",
            'root/plain.py': '',
            'root/standalone.py': '# @om-lite\n',
            'root/script.py': '# @om-lite\n# @om-script\n',
            'root/nonlite_script.py': '# @om-script\n',
            'root/litepkg/__init__.py': '# @om-lite\n',
            'root/litepkg/inherited.py': '',
            'root/litepkg/marked.py': '# @om-lite\n',
            'root/litepkg/nested/__init__.py': '# @om-lite\n',
            'root/litepkg/nested/inherited.py': '',
            'root/litepkg/data.txt': '# @om-lite\n',
        }
        for rel, src in files.items():
            fp = os.path.join(src_dir, rel)
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            with open(fp, 'w') as f:
                f.write(src)

        root = os.path.join(src_dir, 'root')
        sources = discover_lite_sources([root])

        def p(rel):
            return os.path.join(root, rel)

        assert isinstance(sources, LiteSourceDiscovery)
        assert sources.lite_files == {
            p('standalone.py'),
            p('script.py'),
            p('litepkg/__init__.py'),
            p('litepkg/marked.py'),
            p('litepkg/nested/__init__.py'),
        }
        assert list(sources.targets) == [
            LiteSourceTarget(p('litepkg/__init__.py'), 'module'),
            LiteSourceTarget(p('litepkg/inherited.py'), 'module'),
            LiteSourceTarget(p('litepkg/marked.py'), 'module'),
            LiteSourceTarget(p('litepkg/nested/__init__.py'), 'module'),
            LiteSourceTarget(p('litepkg/nested/inherited.py'), 'module'),
            LiteSourceTarget(p('script.py'), 'script'),
            LiteSourceTarget(p('standalone.py'), 'module'),
        ]

        # Both overlapping roots and inherited markers must not duplicate targets.
        assert discover_lite_sources([root, p('litepkg'), root]) == sources


def test_discover_lite_sources_empty():
    assert discover_lite_sources([]) == LiteSourceDiscovery(frozenset(), [])
    with temp_dir_context() as src_dir:
        with open(os.path.join(src_dir, 'plain.py'), 'w') as f:
            f.write('# @om-script\n')
        assert discover_lite_sources([src_dir]) == LiteSourceDiscovery(frozenset(), [])
