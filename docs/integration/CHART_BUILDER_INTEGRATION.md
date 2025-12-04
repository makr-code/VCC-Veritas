"""
Integration des Chart Builders in die Haupt-VERITAS-App

Dieser Code zeigt, wie der Chart Builder in das Hauptmenü
der VERITAS-App integriert werden kann.
"""

# Beispiel-Integration in frontend/veritas_app.py

# ========== IMPORT-BEREICH ==========

# Zu den bestehenden Imports hinzufügen:
from frontend.ui.chart_builder import ChartBuilderWindow


# ========== MENUBAR-BEREICH ==========

# Im menubar-Setup (z.B. in der _create_menubar() Methode):

def _create_menubar(self):
    """Create menubar with File, Tools, Help menus"""
    menubar = tk.Menu(self.root)
    self.root.config(menu=menubar)

    # ... existing menus (File, Edit, etc.) ...

    # ========== NEUES TOOLS-MENU ==========
    tools_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="🛠️ Tools", menu=tools_menu)

    # Chart Builder
    tools_menu.add_command(
        label="📊 Chart Builder",
        command=self._open_chart_builder,
        accelerator="Ctrl+Shift+C"
    )

    tools_menu.add_separator()

    # ... weitere Tools ...

    # Keyboard Shortcut binden
    self.root.bind('<Control-Shift-c>', lambda e: self._open_chart_builder())


# ========== HANDLER-METHODE ==========

def _open_chart_builder(self):
    """Chart Builder-Fenster öffnen"""
    try:
        # Prüfen ob Backend erreichbar ist
        if not hasattr(self, 'api_client'):
            messagebox.showerror(
                "Fehler",
                "API-Client nicht verfügbar. Starten Sie bitte das Backend."
            )
            return

        # Chart Builder öffnen
        ChartBuilderWindow(self.root, self.api_client)

        self.logger.info("Chart Builder geöffnet")

    except Exception as e:
        self.logger.error(f"Fehler beim Öffnen des Chart Builders: {e}", exc_info=True)
        messagebox.showerror(
            "Fehler",
            f"Chart Builder konnte nicht geöffnet werden:\n{e}"
        )


# ========== TOOLBAR-INTEGRATION (Optional) ==========

def _create_toolbar(self):
    """Create toolbar with quick-access buttons"""
    toolbar = ttk.Frame(self.root)
    toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)

    # ... existing toolbar buttons ...

    # Chart Builder Button
    chart_btn = ttk.Button(
        toolbar,
        text="📊 Charts",
        command=self._open_chart_builder,
        width=10
    )
    chart_btn.pack(side=tk.LEFT, padx=2)

    # ... weitere Toolbar-Buttons ...


# ========== ALTERNATIVE: KONTEXTMENÜ ==========

def _create_context_menu(self):
    """Create context menu for chat area"""
    context_menu = tk.Menu(self.chat_display, tearoff=0)

    # ... existing context menu items ...

    context_menu.add_separator()
    context_menu.add_command(
        label="📊 Daten als Chart visualisieren",
        command=self._visualize_as_chart
    )

    # Bind to right-click
    self.chat_display.bind("<Button-3>", lambda e: context_menu.tk_popup(e.x_root, e.y_root))


def _visualize_as_chart(self):
    """
    Selektierten Text als Chart-Prompt verwenden
    """
    try:
        # Get selected text
        try:
            selected_text = self.chat_display.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            selected_text = ""

        if not selected_text:
            messagebox.showinfo(
                "Info",
                "Bitte markieren Sie einen Text, der als Chart-Beschreibung "
                "verwendet werden soll."
            )
            return

        # Chart Builder öffnen mit vorbefülltem Prompt
        builder = ChartBuilderWindow(self.root, self.api_client)

        # Prompt setzen
        builder.prompt_text.delete('1.0', tk.END)
        builder.prompt_text.insert('1.0', selected_text)

        self.logger.info(f"Chart Builder mit Prompt geöffnet: {selected_text[:50]}")

    except Exception as e:
        self.logger.error(f"Fehler bei Chart-Visualisierung: {e}", exc_info=True)


# ========== VERWENDUNGSBEISPIELE ==========

"""
Verwendung in der Haupt-App:

1. Tools-Menü:
   Tools > Chart Builder öffnen

2. Keyboard Shortcut:
   Ctrl+Shift+C

3. Toolbar:
   Klick auf "📊 Charts"-Button

4. Kontextmenü:
   Rechtsklick im Chat > "Daten als Chart visualisieren"

5. Programmatisch:
   self._open_chart_builder()
"""


# ========== VOLLSTÄNDIGES BEISPIEL ==========

"""
Vollständige Integration in eine bestehende Tkinter-App:

import tkinter as tk
from tkinter import ttk, messagebox
from frontend.ui.chart_builder import ChartBuilderWindow
from frontend.api_client import APIClient


class VeritasApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("VERITAS - AI-gestützte Verwaltungsrecherche")

        # API-Client
        self.api_client = APIClient("http://localhost:5000")

        # UI erstellen
        self._create_menubar()
        self._create_toolbar()

        # ... rest of app ...

    def _create_menubar(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Tools-Menü
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="🛠️ Tools", menu=tools_menu)

        tools_menu.add_command(
            label="📊 Chart Builder",
            command=self._open_chart_builder
        )

    def _create_toolbar(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)

        ttk.Button(
            toolbar,
            text="📊 Charts",
            command=self._open_chart_builder
        ).pack(side=tk.LEFT, padx=2)

    def _open_chart_builder(self):
        try:
            ChartBuilderWindow(self.root, self.api_client)
        except Exception as e:
            messagebox.showerror("Fehler", f"Chart Builder-Fehler:\n{e}")

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    app = VeritasApp()
    app.run()
"""
