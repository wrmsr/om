from omcore import lang
from omcore import marshal as msh
from omcore.formats.json import all as json

from ..collection import PermissionRules
from ..types import PermissionRule
from ..types import PermissionState


with lang.auto_proxy_import(globals()):
    from ...fs import permissions as fs
    from ...web import permissions as url


def make_rules() -> PermissionRules:
    return PermissionRules([
        PermissionRule(
            url.RegexUrlPermissionMatcher('https://google.com/.*'),
            PermissionState.DENY,
        ),
        PermissionRule(
            url.RegexUrlPermissionMatcher('https://baidu.com/.*', methods=['POST']),
            PermissionState.DENY,
        ),
        PermissionRule(
            fs.GlobFsPermissionMatcher('**/*.py'),
            PermissionState.ASK,
        ),
        PermissionRule(
            fs.GlobFsPermissionMatcher('**/*.exe', modes=['r']),
            PermissionState.DENY,
        ),
    ])


def test_marshal():
    rules = make_rules()

    j = json.dumps_pretty(msh.marshal(rules))
    print(j)

    rules2 = msh.unmarshal(json.loads(j), PermissionRules)
    assert rules2 == rules


def test_unmarshal():
    mv = {
        'rules': [
            {
                'matcher': {
                    'regex_url': {
                        'pat': 'https://google.com/.*',
                    },
                },
                'result': 'DENY',
            },
            {
                'matcher': {
                    'regex_url': {
                        'pat': 'https://baidu.com/.*',
                        'methods': [
                            'POST',
                        ],
                    },
                },
                'result': 'DENY',
            },
            {
                'matcher': {
                    'glob_fs': {
                        'glob': '**/*.py',
                    },
                },
                'result': 'ASK',
            },
            {
                'matcher': {
                    'glob_fs': {
                        'glob': '**/*.exe',
                        'modes': [
                            'r',
                        ],
                    },
                },
                'result': 'DENY',
            },
        ],
    }

    rules = msh.unmarshal(mv, PermissionRules)

    rules2 = make_rules()
    assert rules2 == rules
