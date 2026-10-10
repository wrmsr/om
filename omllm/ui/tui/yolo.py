"""
permission_rules.append(
    agn.PermissionRule(
        agn.ToolPermissionMatcher(
            tool='ripgrep',
            child=agn.ExecPermissionMatcher(),
        ),
        agn.PermissionState.ALLOW,
    ),
)
"""
from omcore import dataclasses as dc

from .config import Config


##


def yolo_process_config(config: Config) -> Config:
    if config.yolo or config.diet_yolo:
        config = dc.replace(
            config,

            # eval=True,
            exec=True,
            fs=True,
            web=True,
        )

    return config


##


def yolo_autoexec(config: Config, cwd: str) -> list[str]:
    if config.yolo:
        return [
            '/permissions clear',

            '/permissions add allow exec {}',

            f'/permissions add allow glob_fs \'{{"glob":"{cwd}/**","modes":["r","w"]}}\'',

            '/permissions add allow regex_url \'{"pat":"https?://.*",methods:["GET"]}\'',

            '/echo "YOLO"',
        ]

    elif config.diet_yolo:
        return [
            '/permissions clear',

            '/permissions add allow tool \'{"tool":"ripgrep","child":{"exec": {}}}\'',

            f'/permissions add allow glob_fs \'{{"glob":"{cwd}/**","modes":["r"]}}\'',
            f'/permissions add ask glob_fs \'{{"glob":"{cwd}/**","modes":["w"]}}\'',

            '/permissions add ask regex_url \'{"pat":"https?://.*",methods:["GET"]}\'',

            '/echo "DIET YOLO"',
        ]

    else:
        return []
