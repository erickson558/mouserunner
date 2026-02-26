"""Backend service for mouse automation."""

from __future__ import annotations

import logging
import random
import threading
from dataclasses import dataclass
from typing import Callable

import pyautogui

logger = logging.getLogger(__name__)


StatusCallback = Callable[[str], None]


@dataclass(frozen=True)
class RunnerConfig:
    """Runtime settings for the automation service."""

    wait_min_seconds: float = 2.0
    wait_max_seconds: float = 6.0
    anti_idle_interval_seconds: float = 60.0
    click_target_x: int = 10
    click_target_y: int = 10
    random_move_min_duration: float = 0.3
    random_move_max_duration: float = 0.8
    click_move_duration: float = 0.5
    auto_start_delay_ms: int = 1000


def build_default_config() -> RunnerConfig:
    """Builds defaults using the current display dimensions."""
    screen_height = pyautogui.size().height
    return RunnerConfig(click_target_y=screen_height - 10)


class MouseRunnerService:
    """Coordinates movement and anti-idle loops."""

    def __init__(self, config: RunnerConfig, on_status: StatusCallback | None = None) -> None:
        self._config = config
        self._on_status = on_status or logger.info
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._running = False
        self._movement_thread: threading.Thread | None = None
        self._anti_idle_thread: threading.Thread | None = None

    @property
    def config(self) -> RunnerConfig:
        return self._config

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def start(self) -> bool:
        """Starts worker threads if not already running."""
        with self._lock:
            if self._running:
                return False
            self._running = True
            self._stop_event.clear()

            self._movement_thread = threading.Thread(
                target=self._movement_loop,
                name="mouse-runner-move",
                daemon=True,
            )
            self._anti_idle_thread = threading.Thread(
                target=self._anti_idle_loop,
                name="mouse-runner-anti-idle",
                daemon=True,
            )
            self._movement_thread.start()
            self._anti_idle_thread.start()

        self._emit("Mouserunner INICIADO")
        return True

    def stop(self) -> bool:
        """Signals workers to stop."""
        movement_thread = None
        anti_idle_thread = None
        with self._lock:
            if not self._running:
                return False
            self._running = False
            self._stop_event.set()
            movement_thread = self._movement_thread
            anti_idle_thread = self._anti_idle_thread
            self._movement_thread = None
            self._anti_idle_thread = None

        current_thread = threading.current_thread()
        for worker in (movement_thread, anti_idle_thread):
            if worker is not None and worker.is_alive() and worker is not current_thread:
                worker.join(timeout=2)

        self._emit("Mouserunner DETENIDO")
        return True

    def _emit(self, message: str) -> None:
        self._on_status(message)

    def _movement_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                width, height = pyautogui.size()
                x = random.randint(0, width - 1)
                y = random.randint(0, height - 1)

                pyautogui.moveTo(
                    x,
                    y,
                    duration=random.uniform(
                        self._config.random_move_min_duration,
                        self._config.random_move_max_duration,
                    ),
                )
                self._emit(f"Mouse movido a: ({x}, {y}) sin clic")

                pyautogui.moveTo(
                    self._config.click_target_x,
                    self._config.click_target_y,
                    duration=self._config.click_move_duration,
                )
                pyautogui.click()
                self._emit(
                    f"Click en boton Inicio: ({self._config.click_target_x}, {self._config.click_target_y})"
                )

                wait_seconds = random.uniform(self._config.wait_min_seconds, self._config.wait_max_seconds)
                self._emit(f"Esperando {wait_seconds:.2f} s...")
                if self._stop_event.wait(wait_seconds):
                    break
            except pyautogui.FailSafeException:
                self._emit("Fail-safe de pyautogui activado. Se detiene el runner.")
                self.stop()
                break
            except Exception as exc:  # pragma: no cover - hardware/OS dependent
                self._emit(f"Error en movimiento: {exc}")
                if self._stop_event.wait(1):
                    break

    def _anti_idle_loop(self) -> None:
        while not self._stop_event.wait(self._config.anti_idle_interval_seconds):
            try:
                x, y = pyautogui.position()
                pyautogui.moveTo(x + 1, y)
                pyautogui.moveTo(x, y)
                self._emit("Anti-inactividad")
            except pyautogui.FailSafeException:
                self._emit("Fail-safe de pyautogui activado en anti-inactividad. Se detiene el runner.")
                self.stop()
                break
            except Exception as exc:  # pragma: no cover - hardware/OS dependent
                self._emit(f"Error en anti-inactividad: {exc}")
                if self._stop_event.wait(1):
                    break
