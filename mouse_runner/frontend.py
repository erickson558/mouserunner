"""Tkinter frontend and tray integration."""

from __future__ import annotations

import locale
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox

from .backend import MouseRunnerService

try:
    import pystray
    from PIL import Image, ImageDraw

    HAS_TRAY = True
except Exception:  # pragma: no cover - optional dependency
    HAS_TRAY = False


TRANSLATIONS = {
    "es": {
        "language": "Idioma",
        "start": "Iniciar (Alt+I)",
        "stop": "Detener (Alt+D)",
        "donate": "Comprame una cerveza",
        "exit": "Salir (Alt+X)",
        "tray_hint": "Cerrar ventana la minimiza a bandeja.",
        "no_tray_hint": "Sin bandeja: cerrar ventana finaliza la app.",
        "tray_unavailable": "pystray/Pillow no disponibles: sin icono de bandeja.",
        "tray_hidden": "Ventana oculta en bandeja. (Doble click en el icono -> Mostrar)",
        "tray_show": "Mostrar ventana",
        "tray_start": "Iniciar",
        "tray_stop": "Detener",
        "tray_exit": "Salir",
        "donation_error": "No se pudo abrir el enlace de donacion.",
        "status_ready": "Listo",
    },
    "en": {
        "language": "Language",
        "start": "Start (Alt+I)",
        "stop": "Stop (Alt+D)",
        "donate": "Buy me a beer",
        "exit": "Exit (Alt+X)",
        "tray_hint": "Closing the window minimizes it to tray.",
        "no_tray_hint": "No tray available: closing window exits app.",
        "tray_unavailable": "pystray/Pillow unavailable: tray icon disabled.",
        "tray_hidden": "Window hidden to tray. (Double click icon -> Show)",
        "tray_show": "Show window",
        "tray_start": "Start",
        "tray_stop": "Stop",
        "tray_exit": "Exit",
        "donation_error": "Could not open donation link.",
        "status_ready": "Ready",
    },
}

DONATION_URL = "https://www.paypal.com/donate/?hosted_button_id=ZABFRXC2P3JQN"


def detect_default_language() -> str:
    """Returns a supported default UI language based on system locale."""
    language = ""
    try:
        current_locale = locale.getlocale()
        language = (current_locale[0] or "").lower() if current_locale else ""
    except Exception:
        language = ""
    return "es" if language.startswith("es") else "en"


class MouseRunnerApp:
    """Desktop GUI that controls the automation service."""

    def __init__(self, service: MouseRunnerService, app_title: str, icon_path: Path | None = None) -> None:
        self._service = service
        self._app_title = app_title
        self._icon_path = icon_path
        self._tray_icon = None
        self._language = detect_default_language()

        self.root = tk.Tk()
        self.root.title(self._app_title)
        self.root.geometry("320x290")
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
        self._service.set_status_callback(self._on_status)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray if HAS_TRAY else self.exit_app)

        if HAS_TRAY:
            threading.Thread(target=self._start_tray, name="mouse-runner-tray", daemon=True).start()
        else:
            print(self._t("tray_unavailable"))

        self.root.after(self._service.config.auto_start_delay_ms, self.start_runner)

    def _t(self, key: str) -> str:
        return TRANSLATIONS.get(self._language, TRANSLATIONS["en"]).get(key, key)

    def _build_ui(self) -> None:
        # Language selector to support runtime i18n without restarting the app.
        lang_row = tk.Frame(self.root)
        lang_row.pack(pady=(10, 4), padx=14, fill="x")

        self.language_label = tk.Label(
            lang_row,
            text=self._t("language"),
            fg="#333333",
            font=("Arial", 9, "bold"),
        )
        self.language_label.pack(side="left")

        self.language_var = tk.StringVar(value=self._language.upper())
        language_menu = tk.OptionMenu(lang_row, self.language_var, "ES", "EN", command=self._on_language_change)
        language_menu.config(width=5)
        language_menu.pack(side="right")

        self.start_button = tk.Button(
            self.root,
            text=self._t("start"),
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.start_runner,
        )
        self.start_button.pack(pady=8, fill="x", padx=14)

        self.stop_button = tk.Button(
            self.root,
            text=self._t("stop"),
            bg="#03A9F4",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.stop_runner,
        )
        self.stop_button.pack(pady=6, fill="x", padx=14)

        self.donate_button = tk.Button(
            self.root,
            text=self._t("donate"),
            bg="#FFC107",
            fg="#111111",
            font=("Arial", 10, "bold"),
            command=self.open_donation_link,
        )
        self.donate_button.pack(pady=6, fill="x", padx=14)

        self.exit_button = tk.Button(
            self.root,
            text=self._t("exit"),
            bg="#F44336",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.exit_app,
        )
        self.exit_button.pack(pady=10, fill="x", padx=14)

        self.hint_label = tk.Label(
            self.root,
            text=self._t("tray_hint") if HAS_TRAY else self._t("no_tray_hint"),
            fg="#333333",
            font=("Arial", 9),
        )
        self.hint_label.pack(pady=(6, 2))

        self.status_label = tk.Label(
            self.root,
            text=self._t("status_ready"),
            fg="#555555",
            font=("Arial", 8),
        )
        self.status_label.pack(pady=(2, 8))

    def _on_language_change(self, language_code: str) -> None:
        self._language = language_code.lower()
        self.language_label.config(text=self._t("language"))
        self.start_button.config(text=self._t("start"))
        self.stop_button.config(text=self._t("stop"))
        self.donate_button.config(text=self._t("donate"))
        self.exit_button.config(text=self._t("exit"))
        self.hint_label.config(text=self._t("tray_hint") if HAS_TRAY else self._t("no_tray_hint"))

    def _on_status(self, message: str) -> None:
        # Status updates can come from worker threads, so marshal updates to Tk main loop.
        self.root.after(0, lambda: self.status_label.config(text=message))
        print(message)

    def start_runner(self) -> None:
        self._service.start()

    def stop_runner(self) -> None:
        self._service.stop()

    def open_donation_link(self) -> None:
        try:
            webbrowser.open(DONATION_URL, new=2)
        except Exception:
            messagebox.showerror(title="MouseRunner", message=self._t("donation_error"))

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
        print(self._t("tray_hidden"))

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
            pystray.MenuItem(self._t("tray_show"), on_show),
            pystray.MenuItem(self._t("tray_start"), on_start),
            pystray.MenuItem(self._t("tray_stop"), on_stop),
            pystray.MenuItem(self._t("tray_exit"), on_exit),
        )
        self._tray_icon = pystray.Icon("MouseRunner", self._tray_image(), self._app_title, menu)
        self._tray_icon.visible = True
        self._tray_icon.run()

    def run(self) -> None:
        self.root.mainloop()
