import logging
import os.path

from omcore.logs import all as logs
from omdev.home.paths import get_home_paths

from ..types import UiId


##


def configure_tui_logging(ui_id: UiId) -> None:
    log_file = os.path.join(get_home_paths().log_dir, 'llm', 'ui', f'{ui_id.v}.log')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logs.configure_standard_logging(
        handler_factory=lambda: logging.FileHandler(log_file, delay=True),
    )
