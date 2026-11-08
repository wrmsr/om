from .... import agent as agn
from ....core import ui
from ..texts import WebTextRenderer
from ..tools import tool_call_args


def test_inline():
    r = WebTextRenderer()

    assert r.render('plain') == 'plain'
    assert r.render('a', 'b') == 'ab'
    assert r.render('a ', ui.Text.style('b', color='red', bold=True)) == [
        'a ',
        {'style': {'color': 'red', 'bold': True}, 'c': 'b'},
    ]


def test_json():
    r = WebTextRenderer()

    out = r.render(ui.JsonText({'a': [1, 'x', None]}, ui.JsonTextStyle(mode='compact')))
    assert out == {'json': [
        [None, '{'],
        ['key', '"a"'],
        [None, ':['],
        ['number', '1'],
        [None, ','],
        ['string', '"x"'],
        [None, ','],
        ['literal', 'null'],
        [None, ']}'],
    ]}


def test_blocks():
    r = WebTextRenderer(ui.TextRenderingOptions(paths=ui.CwdDisplayPathResolver('/proj')))

    assert r.render(ui.MarkdownText('# hi')) == {'md': '# hi'}

    out = r.render(ui.DiffText(old='a\nb\n', new='a\nc\n', path='/proj/src/x.py'))
    assert out == {'diff': {
        'path': 'src/x.py',
        'lines': [
            '--- src/x.py\n',
            '+++ src/x.py\n',
            '@@ -1,2 +1,2 @@\n',
            ' a\n',
            '-b\n',
            '+c\n',
        ],
    }}


def test_tool_call_args():
    ctx = agn.ToolContext(args={'path': 'x', 'contents': 'a' * 10, 'n': [1, {'s': 'b' * 3}], 'o': object})

    assert tool_call_args(ctx, max_str_chars=4) == {
        'path': 'x',
        'contents': 'aaaa... (6 characters not shown)',
        'n': [1, {'s': 'bbb'}],
        'o': '<cla... (12 characters not shown)',
    }
