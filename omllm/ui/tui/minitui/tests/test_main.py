from ..main import _parse_config


##


def test_yolo_argument():
    config = _parse_config(['--yolo'])

    assert config.yolo
    assert config.eval
    assert config.exec
    assert config.fs
