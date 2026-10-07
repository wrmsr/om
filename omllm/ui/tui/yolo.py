from omcore import dataclasses as dc

from .config import Config


##


def yolo_process_config(config: Config) -> Config:
    if config.yolo:
        config = dc.replace(
            config,

            eval=True,
            exec=True,
            fs=True,
        )

    return config


##


def yolo_autoexec(cwd: str) -> list[str]:
    return [
        '/permissions clear',
        '/permissions add allow exec {}',
        f'/permissions add allow glob_fs \'{{"glob":"{cwd}/**","modes":["r","w"]}}\'',
        '/echo "YOLO"',
    ]
