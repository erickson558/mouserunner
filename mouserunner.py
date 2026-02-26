"""MouseRunner entrypoint."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from mouse_runner import MouseRunnerApp, MouseRunnerService, build_default_config


def configure_logging() -> None:
    """Configures basic console logging for runtime events."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


def main() -> None:
    configure_logging()
    config = build_default_config()
    service = MouseRunnerService(config=config)
    if getattr(sys, "frozen", False):
        base_path = Path(getattr(sys, "_MEIPASS", Path.cwd()))
    else:
        base_path = Path(__file__).resolve().parent
    icon_path = base_path / "mouserunner.ico"
    app = MouseRunnerApp(service=service, app_title="MouseRunner v1.9", icon_path=icon_path)
    app.run()


if __name__ == "__main__":
    main()
