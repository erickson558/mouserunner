# MouseRunner V1.9.1

Aplicacion de automatizacion de mouse con interfaz Tkinter y soporte de bandeja del sistema.

## Caracteristicas

- Arquitectura separada por capas:
  - `mouse_runner/backend.py`: logica y ciclos de automatizacion
  - `mouse_runner/frontend.py`: interfaz y eventos de usuario
- Soporte multi idioma (espanol e ingles)
- Boton de donaciones "Comprame una cerveza"
- Soporte de icono `.ico` en app y build
- Build reproducible de ejecutable con PyInstaller

## Version

- Version actual: `V1.9.1`
- Tipo de cambio: `patch` (correcciones de estabilidad y empaquetado)

## Ejecutar en desarrollo

```bash
python mouserunner.py
```

## Generar EXE

```bash
pyinstaller --clean --noconfirm mouserunner.spec
```

Copiar el ejecutable generado a la raiz del proyecto:

```bash
copy .\dist\mouserunner.exe .\mouserunner.exe
```

## Dependencias

Ver `requirements.txt`.
