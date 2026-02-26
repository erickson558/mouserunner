"""Tkinter frontend and tray integration."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path

from .backend import MouseRunnerService

try:
    import pystray
    from PIL import Image, ImageDraw

    HAS_TRAY = True
except Exception:  # pragma: no cover - optional dependency
    HAS_TRAY = False


class MouseRunnerApp:
    """Desktop GUI that controls the automation service."""

    def __init__(self, service: MouseRunnerService, app_title: str, icon_path: Path | None = None) -> None:
        self._service = service
        self._app_title = app_title
        self._icon_path = icon_path
        self._tray_icon = None

        self.root = tk.Tk()
        self.root.title(self._app_title)
        self.root.geometry("280x190")
        self.root.resizable(False, False)

        if self._icon_path and self._icon_path.exists():
            try:
                self.root.iconbitmap(default=str(self._icon_path))
            except Exception:
                pass

        self.root.bind_all("<Alt-i>", lambda _: self.start_runner())
        self.root.bind_all("<Alt-d>", lambda _: self.stop_runner())
        self.root.bind_all("<Alt-x>", lambda _: self.exit_app())

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray if HAS_TRAY else self.exit_app)

        if HAS_TRAY:
            threading.Thread(target=self._start_tray, name="mouse-runner-tray", daemon=True).start()
        else:
            print("pystray/Pillow no disponibles: sin icono de bandeja.")

        self.root.after(self._service.config.auto_start_delay_ms, self.start_runner)

    def _build_ui(self) -> None:
        tk.Button(
            self.root,
            text="Iniciar (Alt+I)",
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.start_runner,
        ).pack(pady=12, fill="x", padx=14)

        tk.Button(
            self.root,
            text="Detener (Alt+D)",
            bg="#03A9F4",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.stop_runner,
        ).pack(pady=6, fill="x", padx=14)

        tk.Button(
            self.root,
            text="Salir (Alt+X)",
            bg="#F44336",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.exit_app,
        ).pack(pady=12, fill="x", padx=14)

        tk.Label(
            self.root,
            text="Cerrar ventana la minimiza a bandeja." if HAS_TRAY else "Sin bandeja: cerrar ventana finaliza la app.",
            fg="#333333",
            font=("Arial", 9),
        ).pack(pady=(10, 2))

    def start_runner(self) -> None:
        self._service.start()

    def stop_runner(self) -> None:
        self._service.stop()

    def exit_app(self) -> None:
        self.stop_runner()
        if HAS_TRAY and self._tray_icon is not None:
            try:
                self._tray_icon.stop()
            except Exception:
                pass
        self.root.destroy()

    def hide_to_tray(self) -> None:
        self.root.withdraw()
        print("Ventana oculta en bandeja. (Doble click en el icono -> Mostrar)")

    def show_window(self) -> None:
        self.root.deiconify()
        self.root.after(0, self.root.lift)

    def _tray_image(self, width: int = 64, height: int = 64):
        if self._icon_path and self._icon_path.exists():
            try:
                return Image.open(self._icon_path)
            except Exception:
                pass

        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((8, 8, width - 8, height - 8), fill=(33, 150, 243, 255))
        draw.text((22, 18), "M", fill=(255, 255, 255, 255))
        return image

    def _start_tray(self) -> None:
        if not HAS_TRAY:
            return

        def on_show(icon, item):
            self.show_window()

        def on_start(icon, item):
            self.start_runner()

        def on_stop(icon, item):
            self.stop_runner()

        def on_exit(icon, item):
            self.root.after(0, self.exit_app)

        menu = pystray.Menu(
            pystray.MenuItem("Mostrar ventana", on_show),
            pystray.MenuItem("Iniciar", on_start),
            pystray.MenuItem("Detener", on_stop),
            pystray.MenuItem("Salir", on_exit),
        )
        self._tray_icon = pystray.Icon("MouseRunner", self._tray_image(), self._app_title, menu)
        self._tray_icon.visible = True
        self._tray_icon.run()

    def run(self) -> None:
        self.root.mainloop()
