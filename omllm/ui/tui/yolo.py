def yolo_autoexec(cwd: str) -> list[str]:
    return [
        '/permissions clear',
        '/permissions add allow exec {}',
        f'/permissions add allow glob_fs \'{{"glob":"{cwd}/**","modes":["r","w"]}}\'',
        '/echo "YOLO"',
    ]
