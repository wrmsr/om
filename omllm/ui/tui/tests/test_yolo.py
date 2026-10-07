from ..config import Config
from ..yolo import yolo_process_config


##


def test_yolo_argument():
    config = Config.parse_from_arguments(['--yolo'])
    config = yolo_process_config(config)

    assert config.yolo
    assert config.eval
    assert config.exec
    assert config.fs
