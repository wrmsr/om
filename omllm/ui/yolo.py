import glob
import os.path
import shlex
import typing as ta

from omcore import dataclasses as dc
from omcore.formats.json import all as json

from .config import UiConfig


UiConfigT = ta.TypeVar('UiConfigT', bound=UiConfig)


##


def yolo_process_config(config: UiConfigT) -> UiConfigT:
    if config.yolo or config.diet_yolo:
        config = dc.replace(
            config,

            # eval=True,
            exec=True,
            fs=True,
            web=True,

            subagents=True,
        )

    return config


##


def _add_cwd_tree_rule_command(
        cwd: str,
        *,
        state: str,
        modes: ta.Sequence[str],
) -> str:
    """
    The command adding a rule over everything beneath the working directory. The directory is data on its way into a
    glob, into json, and into a command line, and is escaped for each: it may hold anything a path may.
    """

    body = json.dumps_compact({
        'glob': os.path.join(glob.escape(cwd), '**'),
        'modes': list(modes),
    })

    return f'/permissions add {state} glob_fs {shlex.quote(body)}'


def yolo_autoexec(config: UiConfig, cwd: str) -> list[str]:
    if config.yolo:
        return [
            '/permissions clear',

            '/permissions add allow exec {}',

            _add_cwd_tree_rule_command(cwd, state='allow', modes=['r', 'w']),

            '/permissions add allow regex_url \'{"pat":"https?://.*",methods:["GET"]}\'',

            # Spawning a subagent is allowed outright. What the subagent then does is asked about, or not, under the
            # same rules as the agent which spawned it.
            '/permissions add allow subagent {}',

            '/echo "YOLO"',
        ]

    elif config.diet_yolo:
        return [
            '/permissions clear',

            '/permissions add allow tool \'{"tool":"ripgrep","child":{"exec": {}}}\'',

            _add_cwd_tree_rule_command(cwd, state='allow', modes=['r']),
            _add_cwd_tree_rule_command(cwd, state='ask', modes=['w']),

            '/permissions add ask regex_url \'{"pat":"https?://.*",methods:["GET"]}\'',

            '/permissions add allow subagent {}',

            '/echo "DIET YOLO"',
        ]

    else:
        return []
