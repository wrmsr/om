from omcore import marshal as msh
from omcore.formats.json import all as json

from ..collection import PermissionRules
from ..fs import GlobFsPermissionMatcher
from ..types import PermissionRule
from ..types import PermissionState
from ..url import RegexUrlPermissionMatcher


def test_marshal():
    rules = PermissionRules([
        PermissionRule(
            RegexUrlPermissionMatcher('https://google.com/.*'),
            PermissionState.DENY,
        ),
        PermissionRule(
            RegexUrlPermissionMatcher('https://baidu.com/.*', methods=['POST']),
            PermissionState.DENY,
        ),
        PermissionRule(
            GlobFsPermissionMatcher('**/*.py'),
            PermissionState.ASK,
        ),
        PermissionRule(
            GlobFsPermissionMatcher('**/*.exe', modes=['r']),
            PermissionState.DENY,
        ),
    ])

    j = json.dumps_pretty(msh.marshal(rules))
    print(j)
