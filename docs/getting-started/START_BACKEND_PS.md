# Start Backend (PowerShell)

This file documents how to start the VERITAS backend on Windows PowerShell using Python 3.13 and a `.venv` virtual environment.

Quick steps

1. Open PowerShell in the repository root (where `.venv` and `start-backend.ps1` live).
2. Create or ensure a Python 3.13 virtualenv at `.venv` and install dependencies (example):

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -3.13 -m pip install -r requirements.txt
```

3. Start the backend (default host 127.0.0.1, port 8000):

```powershell
# From repository root
.\start-backend.ps1

# With custom options
.\start-backend.ps1 -Host 0.0.0.0 -Port 8080 -Workers 2
```

Notes

- The script assumes the ASGI app is exposed as `backend.main:app`. If your entrypoint is different, edit `start-backend.ps1` and change the `$asgiTarget` variable.
- `uvloop` is optional and only used if installed and supported on Windows (uvloop has limited Windows support). If you have an alternative event loop, adapt the script accordingly.
- If `.venv` is not found the script will fall back to the system Python; prefer using the `.venv`.

If you want, I can adapt the script to detect common ASGI entrypoints automatically (e.g., `backend.main`, `main_backend.py`) or create a `start-backend.bat` for cmd.exe as well.
