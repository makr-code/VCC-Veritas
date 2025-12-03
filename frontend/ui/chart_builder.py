"""
Chart Builder UI - Tkinter-Fenster für interaktive Chart-Erstellung

Features:
- Prompt-Eingabe für Chart-Generierung
- Template-Auswahl
- Live-Preview
- Export zu PNG, SVG, PDF, PPTX
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import base64
from io import BytesIO
import logging
import asyncio
import shutil
from pathlib import Path

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL nicht verfügbar, Bildanzeige eingeschränkt")

logger = logging.getLogger(__name__)


class ChartBuilderWindow:
    """
    Tkinter-Fenster für interaktive Chart-Erstellung
    
    Integration mit VERITAS Backend Chart-API
    """
    
    def __init__(self, parent, api_client):
        """
        Args:
            parent: Tkinter-Parent-Widget
            api_client: API-Client für Backend-Kommunikation
        """
        self.window = tk.Toplevel(parent)
        self.window.title("VERITAS - Vector Chart Builder 📊")
        self.window.geometry("1400x900")
        
        self.api_client = api_client
        self.current_chart = None
        self.templates = []
        
        self._create_ui()
        self._load_templates()
        
        logger.info("ChartBuilderWindow initialisiert")
    
    def _create_ui(self):
        """UI-Elemente erstellen"""
        
        # Hauptcontainer mit horizontaler Aufteilung
        main_paned = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # --- Linke Spalte: Eingabe & Optionen (400px) ---
        left_frame = ttk.Frame(main_paned, width=400)
        main_paned.add(left_frame, weight=0)
        
        # --- Rechte Spalte: Chart-Preview ---
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)
        
        # ========== LINKE SPALTE ==========
        
        # Header
        header_label = ttk.Label(
            left_frame, 
            text="🎨 AI-gestützte Chart-Generierung",
            font=("Arial", 14, "bold")
        )
        header_label.pack(pady=(10, 20), padx=10)
        
        # Scrollbarer Container
        canvas = tk.Canvas(left_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=(10, 0))
        scrollbar.pack(side="right", fill="y")
        
        # Prompt-Eingabe
        prompt_section = ttk.LabelFrame(scrollable_frame, text="📝 Chart-Beschreibung", padding=10)
        prompt_section.pack(fill=tk.X, pady=(0, 15), padx=10)
        
        self.prompt_text = scrolledtext.ScrolledText(
            prompt_section,
            height=6,
            wrap=tk.WORD,
            font=("Arial", 10)
        )
        self.prompt_text.pack(fill=tk.BOTH, expand=True)
        
        # Placeholder-Text
        placeholder = """Beispiele:
• Erstelle ein Bar Chart mit BImSchG-Anlagen pro Kategorie
• Zeige Liniendiagramm der WKA-Leistung über Zeit
• Pie Chart: Verteilung der Anlagentypen
• Scatter Plot: Leistung vs. Nabenhöhe"""
        
        self.prompt_text.insert('1.0', placeholder)
        self.prompt_text.tag_add("placeholder", "1.0", "end")
        self.prompt_text.tag_config("placeholder", foreground="gray")
        
        # Placeholder-Handler
        def on_focus_in(event):
            if self.prompt_text.tag_ranges("placeholder"):
                self.prompt_text.delete('1.0', tk.END)
                self.prompt_text.tag_remove("placeholder", "1.0", "end")
        
        def on_focus_out(event):
            if not self.prompt_text.get('1.0', tk.END).strip():
                self.prompt_text.insert('1.0', placeholder)
                self.prompt_text.tag_add("placeholder", "1.0", "end")
                self.prompt_text.tag_config("placeholder", foreground="gray")
        
        self.prompt_text.bind("<FocusIn>", on_focus_in)
        self.prompt_text.bind("<FocusOut>", on_focus_out)
        
        # Generieren-Button
        generate_btn = ttk.Button(
            prompt_section,
            text="🚀 Chart Generieren",
            command=self._on_generate_click
        )
        generate_btn.pack(fill=tk.X, pady=(10, 0))
        
        # Vorlagen-Auswahl
        templates_section = ttk.LabelFrame(scrollable_frame, text="📋 Vorlagen", padding=10)
        templates_section.pack(fill=tk.X, pady=(0, 15), padx=10)
        
        # Template-Buttons werden dynamisch geladen
        self.template_buttons_frame = ttk.Frame(templates_section)
        self.template_buttons_frame.pack(fill=tk.X)
        
        # Export-Optionen
        export_section = ttk.LabelFrame(scrollable_frame, text="💾 Export", padding=10)
        export_section.pack(fill=tk.X, pady=(0, 15), padx=10)
        
        export_buttons_frame = ttk.Frame(export_section)
        export_buttons_frame.pack(fill=tk.X)
        
        ttk.Button(
            export_buttons_frame,
            text="PNG",
            command=lambda: self._export('png'),
            width=8
        ).pack(side=tk.LEFT, padx=2, pady=2)
        
        ttk.Button(
            export_buttons_frame,
            text="SVG",
            command=lambda: self._export('svg'),
            width=8
        ).pack(side=tk.LEFT, padx=2, pady=2)
        
        ttk.Button(
            export_buttons_frame,
            text="PDF",
            command=lambda: self._export('pdf'),
            width=8
        ).pack(side=tk.LEFT, padx=2, pady=2)
        
        ttk.Button(
            export_buttons_frame,
            text="PPTX",
            command=lambda: self._export('pptx'),
            width=8
        ).pack(side=tk.LEFT, padx=2, pady=2)
        
        # Hilfe-Text
        help_section = ttk.LabelFrame(scrollable_frame, text="ℹ️ Hilfe", padding=10)
        help_section.pack(fill=tk.X, pady=(0, 15), padx=10)
        
        help_text = tk.Text(help_section, height=8, wrap=tk.WORD, font=("Arial", 9))
        help_text.pack(fill=tk.BOTH, expand=True)
        help_text.insert('1.0', """Unterstützte Chart-Typen:
• Bar Chart (Balkendiagramm)
• Line Chart (Liniendiagramm)
• Pie Chart (Kreisdiagramm)
• Scatter Plot (Streudiagramm)
• Heatmap (Wärmekarte)

Powered by:
• Matplotlib & Seaborn
• On-Premise LLM (Ollama/vLLM)
• RAG-Daten aus VERITAS""")
        help_text.config(state=tk.DISABLED, bg="#f0f0f0")
        
        # ========== RECHTE SPALTE ==========
        
        # Preview-Header
        preview_header = ttk.Frame(right_frame)
        preview_header.pack(fill=tk.X, pady=(10, 5), padx=10)
        
        ttk.Label(
            preview_header,
            text="👁️ Vorschau",
            font=("Arial", 12, "bold")
        ).pack(side=tk.LEFT)
        
        self.chart_info_label = ttk.Label(preview_header, text="", font=("Arial", 9))
        self.chart_info_label.pack(side=tk.RIGHT)
        
        # Canvas für Chart-Anzeige
        self.canvas_frame = ttk.Frame(right_frame, relief=tk.SUNKEN, borderwidth=2)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Placeholder
        self.placeholder_label = ttk.Label(
            self.canvas_frame,
            text="Chart wird hier angezeigt...\n\n"
                 "Geben Sie eine Beschreibung ein und klicken Sie auf 'Generieren'\n"
                 "oder wählen Sie eine Vorlage aus",
            font=("Arial", 11),
            foreground='gray',
            justify=tk.CENTER
        )
        self.placeholder_label.pack(expand=True)
    
    def _load_templates(self):
        """Verfügbare Templates vom Backend laden"""
        try:
            # Asynchroner API-Call (vereinfacht für Tkinter)
            # In echter Implementierung: asyncio.run() oder Thread
            import requests
            
            response = requests.get(f"{self.api_client.base_url}/api/charts/templates")
            
            if response.status_code == 200:
                self.templates = response.json()
                self._render_template_buttons()
                logger.info(f"{len(self.templates)} Templates geladen")
            else:
                logger.warning(f"Templates konnten nicht geladen werden: {response.status_code}")
                self._render_fallback_templates()
        
        except Exception as e:
            logger.error(f"Fehler beim Laden der Templates: {e}")
            self._render_fallback_templates()
    
    def _render_template_buttons(self):
        """Template-Buttons rendern"""
        for widget in self.template_buttons_frame.winfo_children():
            widget.destroy()
        
        for template in self.templates:
            icon = {
                'bar': '📊',
                'line': '📈',
                'pie': '🥧',
                'scatter': '⚫',
                'heatmap': '🔥'
            }.get(template['type'], '📊')
            
            btn = ttk.Button(
                self.template_buttons_frame,
                text=f"{icon} {template['title']}",
                command=lambda t=template: self._load_template(t)
            )
            btn.pack(fill=tk.X, pady=2)
    
    def _render_fallback_templates(self):
        """Fallback-Templates wenn Backend nicht erreichbar"""
        fallback = [
            {"name": "example_bar", "title": "Beispiel Bar Chart", "type": "bar"},
            {"name": "example_pie", "title": "Beispiel Pie Chart", "type": "pie"},
            {"name": "example_line", "title": "Beispiel Line Chart", "type": "line"}
        ]
        self.templates = fallback
        self._render_template_buttons()
    
    def _load_template(self, template):
        """Vorlage laden und Prompt setzen"""
        template_prompts = {
            'bimschg_overview': "Erstelle ein Bar Chart mit BImSchG-Anlagen gruppiert nach 4. BImSchV-Nummer",
            'wka_leistung': "Zeige ein Pie Chart der WKA-Gesamtleistung aufgeteilt nach Status",
            'anlagenverteilung': "Erstelle ein Pie Chart der Anlagentypen-Verteilung",
            'zeitreihe_genehmigungen': "Liniendiagramm: Anzahl Genehmigungen pro Jahr (2010-2024)"
        }
        
        prompt = template_prompts.get(
            template['name'],
            f"Erstelle ein {template['type']} Chart: {template['title']}"
        )
        
        # Placeholder entfernen
        if self.prompt_text.tag_ranges("placeholder"):
            self.prompt_text.delete('1.0', tk.END)
            self.prompt_text.tag_remove("placeholder", "1.0", "end")
        else:
            self.prompt_text.delete('1.0', tk.END)
        
        self.prompt_text.insert('1.0', prompt)
        
        # Automatisch generieren
        self._on_generate_click(template=template['name'])
    
    def _on_generate_click(self, template=None):
        """Chart generieren (Button-Handler)"""
        prompt = self.prompt_text.get('1.0', tk.END).strip()
        
        # Validierung
        if self.prompt_text.tag_ranges("placeholder") or not prompt:
            messagebox.showwarning(
                "Eingabe fehlt",
                "Bitte geben Sie eine Chart-Beschreibung ein."
            )
            return
        
        # Loading-Indikator
        self._show_loading()
        
        # Asynchrone Generierung in Thread
        import threading
        thread = threading.Thread(
            target=self._generate_chart_sync,
            args=(prompt, template)
        )
        thread.start()
    
    def _generate_chart_sync(self, prompt, template=None):
        """Chart generieren (synchrone Wrapper-Methode)"""
        try:
            import requests
            
            payload = {"prompt": prompt}
            if template:
                payload["template"] = template
            
            response = requests.post(
                f"{self.api_client.base_url}/api/charts/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                chart_data = response.json()
                
                # UI-Update im Main-Thread
                self.window.after(0, self._display_chart, chart_data)
            else:
                error_msg = response.json().get('detail', 'Unbekannter Fehler')
                self.window.after(0, self._show_error, error_msg)
        
        except Exception as e:
            logger.error(f"Chart-Generierung fehlgeschlagen: {e}", exc_info=True)
            self.window.after(0, self._show_error, str(e))
    
    def _display_chart(self, chart_data):
        """Chart im Canvas anzeigen"""
        try:
            self.current_chart = chart_data
            
            # Placeholder entfernen
            if hasattr(self, 'placeholder_label') and self.placeholder_label.winfo_exists():
                self.placeholder_label.destroy()
            
            # Alte Widgets entfernen
            for widget in self.canvas_frame.winfo_children():
                widget.destroy()
            
            if not PIL_AVAILABLE:
                # Fallback ohne PIL
                label = ttk.Label(
                    self.canvas_frame,
                    text=f"Chart generiert: {chart_data.get('title', 'Chart')}\n"
                         f"Typ: {chart_data.get('chart_type', 'unknown')}\n\n"
                         f"(PIL nicht verfügbar für Bildanzeige)\n"
                         f"Nutzen Sie Export-Funktionen zum Speichern.",
                    justify=tk.CENTER
                )
                label.pack(expand=True)
                return
            
            # Decode Base64 image
            img_data = base64.b64decode(chart_data['image_base64'])
            img = Image.open(BytesIO(img_data))
            
            # Skalieren für Anzeige (max 1000px breit)
            max_width = 1000
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # Display
            label = tk.Label(self.canvas_frame, image=photo, bg='white')
            label.image = photo  # Keep reference!
            label.pack(expand=True)
            
            # Info-Label aktualisieren
            self.chart_info_label.config(
                text=f"{chart_data.get('chart_type', '').upper()} | "
                     f"{chart_data.get('title', 'Chart')}"
            )
            
            logger.info(f"Chart angezeigt: {chart_data.get('title')}")
        
        except Exception as e:
            logger.error(f"Fehler beim Anzeigen des Charts: {e}", exc_info=True)
            self._show_error(f"Chart-Anzeige fehlgeschlagen: {e}")
        
        finally:
            self._hide_loading()
    
    def _export(self, format_type):
        """Chart exportieren"""
        if not self.current_chart:
            messagebox.showwarning(
                "Kein Chart",
                "Bitte generieren Sie zuerst ein Chart."
            )
            return
        
        # Datei-Dialog
        filetypes = {
            'png': [("PNG Image", "*.png")],
            'svg': [("SVG Vector", "*.svg")],
            'pdf': [("PDF Document", "*.pdf")],
            'pptx': [("PowerPoint", "*.pptx")]
        }
        
        default_name = self.current_chart.get('title', 'chart').replace(' ', '_')
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=f".{format_type}",
            initialfile=f"{default_name}.{format_type}",
            filetypes=filetypes[format_type]
        )
        
        if not filepath:
            return
        
        try:
            # Server-Pfad
            server_path = self.current_chart['exports'].get(format_type)
            
            if not server_path or not Path(server_path).exists():
                messagebox.showerror(
                    "Export-Fehler",
                    f"{format_type.upper()}-Datei nicht auf Server gefunden."
                )
                return
            
            # Datei kopieren
            shutil.copy(server_path, filepath)
            
            messagebox.showinfo(
                "Export erfolgreich",
                f"Chart gespeichert als:\n{filepath}"
            )
            logger.info(f"Chart exportiert: {filepath}")
        
        except Exception as e:
            logger.error(f"Export-Fehler: {e}", exc_info=True)
            messagebox.showerror(
                "Export-Fehler",
                f"Fehler beim Exportieren:\n{e}"
            )
    
    def _show_loading(self):
        """Loading-Indikator anzeigen"""
        # Einfache Implementierung: Label ändern
        if hasattr(self, 'placeholder_label') and self.placeholder_label.winfo_exists():
            self.placeholder_label.config(
                text="⏳ Chart wird generiert...\nBitte warten...",
                foreground='blue'
            )
    
    def _hide_loading(self):
        """Loading-Indikator verstecken"""
        # Wird durch _display_chart ersetzt
        pass
    
    def _show_error(self, error_msg):
        """Fehler anzeigen"""
        self._hide_loading()
        
        messagebox.showerror(
            "Fehler",
            f"Chart-Generierung fehlgeschlagen:\n\n{error_msg}"
        )
        
        # Placeholder wiederherstellen
        if not hasattr(self, 'placeholder_label') or not self.placeholder_label.winfo_exists():
            for widget in self.canvas_frame.winfo_children():
                widget.destroy()
            
            self.placeholder_label = ttk.Label(
                self.canvas_frame,
                text="❌ Fehler bei der Chart-Generierung\n\n"
                     "Bitte versuchen Sie es erneut.",
                font=("Arial", 11),
                foreground='red',
                justify=tk.CENTER
            )
            self.placeholder_label.pack(expand=True)


# Standalone-Test
if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    root = tk.Tk()
    root.withdraw()
    
    # Mock API-Client
    class MockAPIClient:
        base_url = "http://localhost:5000"
    
    api_client = MockAPIClient()
    
    window = ChartBuilderWindow(root, api_client)
    
    root.mainloop()
