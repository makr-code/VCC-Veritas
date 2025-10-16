"""
VERITAS Protected Module
WARNING: This file contains embedded protection keys. 
Modification will be detected and may result in license violations.
"""

# === VERITAS PROTECTION KEYS (DO NOT MODIFY) ===
module_name = "veritas_ui_components"
module_licenced_organization = "VERITAS_TECH_GMBH"
module_licence_key = "eyJjbGllbnRfaWQi...UwzzMA=="  # Gekuerzt fuer Sicherheit
module_organization_key = "8cfe2d25d8fd848c68bca51ea074da4f67824604508d635a66ac4791ae5e6f50"
module_file_key = "489d18a4f32c539a2db70cd87c1ef94a3cc25a577ca539cf627eec81f57ab700"
module_version = "1.0"
module_protection_level = 1
# === END PROTECTION KEYS ===
"""
UI-Hilfselemente für Veritas RAG Chat
Enthält Tooltip und andere UI-Komponenten
"""

import tkinter as tk


class Tooltip:
    """
    Erweiterte Tooltip-Klasse für GUI-Elemente
    
    Features:
    - Einfache Textanzeige
    - Optional: Klickbarer Link mit Callback
    - Multi-line Support
    """
    def __init__(self, widget, text, link_text=None, link_callback=None):
        """
        Args:
            widget: Tkinter Widget für Tooltip
            text: Tooltip-Text (Multi-line mit \n)
            link_text: Optional: Text für klickbaren Link
            link_callback: Optional: Callback-Funktion beim Link-Klick
        """
        self.widget = widget
        self.text = text
        self.link_text = link_text
        self.link_callback = link_callback
        self.tipwindow = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tipwindow or not self.text:
            return
        try:
            x, y, cx, cy = self.widget.bbox("insert")
        except:
            x, y, cx, cy = (0, 0, 0, 0)
        x = x + self.widget.winfo_rootx() + 30
        y = y + self.widget.winfo_rooty() + 30
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        # Frame für Tooltip-Inhalt
        frame = tk.Frame(tw, relief="solid", borderwidth=1, bg="#FFFFDD")
        frame.pack()
        
        # Haupttext
        label = tk.Label(
            frame, 
            text=self.text, 
            justify=tk.LEFT,
            bg="#FFFFDD",
            padx=8, 
            pady=5,
            font=('Segoe UI', 9)
        )
        label.pack()
        
        # Optional: Klickbarer Link
        if self.link_text and self.link_callback:
            link_label = tk.Label(
                frame,
                text=self.link_text,
                fg="#0066CC",
                bg="#FFFFDD",
                cursor="hand2",
                font=('Segoe UI', 9, 'underline'),
                padx=8,
                pady=3
            )
            link_label.pack()
            link_label.bind("<Button-1>", lambda e: self._on_link_click())

    def _on_link_click(self):
        """Behandelt Link-Klick"""
        if self.link_callback:
            try:
                self.link_callback()
            except Exception as e:
                print(f"Tooltip Link-Callback Fehler: {e}")
        # Tooltip schließen nach Klick
        self.hide_tip()

    def hide_tip(self, event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


# ✨ Feature #1: Collapsible Sections
class CollapsibleSection:
    """
    Wiederverwendbare Collapsible Section für Text-Widgets
    
    Ermöglicht Expand/Collapse von Sections mit:
    - Toggle-Icons (▶/▼)
    - Click-Handler
    - State-Management
    - Optional: Animation
    
    Usage:
        section = CollapsibleSection(
            text_widget=chat_text,
            section_id="sources_123",
            title="📚 Quellen (5)",
            initially_collapsed=True,
            parent_window=window
        )
        section.insert_content(lambda: insert_sources_here())
    """
    
    def __init__(
        self,
        text_widget: tk.Text,
        section_id: str,
        title: str,
        initially_collapsed: bool = False,
        parent_window: tk.Tk = None,
        animate: bool = True
    ):
        """
        Args:
            text_widget: Tkinter Text Widget
            section_id: Eindeutige ID für diese Section (z.B. "sources_msg_123")
            title: Anzeigetitel (z.B. "📚 Quellen (5)")
            initially_collapsed: Initial collapsed State (True = eingeklappt)
            parent_window: Parent Window für Animationen
            animate: Animation aktivieren (True = smooth expand/collapse)
        """
        self.text_widget = text_widget
        self.section_id = section_id
        self.title = title
        self.is_collapsed = initially_collapsed
        self.parent_window = parent_window
        self.animate = animate
        
        # Tags für diese Section
        self.header_tag = f"collapsible_header_{section_id}"
        self.content_tag = f"collapsible_content_{section_id}"
        self.arrow_tag = f"collapsible_arrow_{section_id}"
        
        # Positions-Tracker
        self.header_start = None
        self.header_end = None
        self.content_start = None
        self.content_end = None
        self.arrow_start = None
        self.arrow_end = None
        
        # Animation State
        self._animation_in_progress = False
    
    def insert_header(self):
        """Fügt Section-Header mit Toggle-Button ein"""
        # Arrow Icon (▶ collapsed, ▼ expanded)
        arrow = "▶" if self.is_collapsed else "▼"
        
        self.arrow_start = self.text_widget.index(tk.END)
        self.text_widget.insert(tk.END, f"{arrow} ", self.arrow_tag)
        self.arrow_end = self.text_widget.index(tk.END)
        
        # Title
        self.header_start = self.text_widget.index(tk.END)
        self.text_widget.insert(tk.END, self.title, self.header_tag)
        self.header_end = self.text_widget.index(tk.END)
        
        self.text_widget.insert(tk.END, "\n")
        
        # Click-Handler für Toggle
        self.text_widget.tag_bind(self.header_tag, "<Button-1>", self._toggle)
        self.text_widget.tag_bind(self.arrow_tag, "<Button-1>", self._toggle)
        
        # Styling
        self.text_widget.tag_configure(self.header_tag, foreground="#0066CC", font=('Segoe UI', 10, 'bold'))
        self.text_widget.tag_configure(self.arrow_tag, foreground="#0066CC")
        
        # Cursor über Events für beide Tags
        self.text_widget.tag_bind(self.header_tag, "<Enter>", lambda e: self.text_widget.config(cursor="hand2"))
        self.text_widget.tag_bind(self.header_tag, "<Leave>", lambda e: self.text_widget.config(cursor=""))
        self.text_widget.tag_bind(self.arrow_tag, "<Enter>", lambda e: self.text_widget.config(cursor="hand2"))
        self.text_widget.tag_bind(self.arrow_tag, "<Leave>", lambda e: self.text_widget.config(cursor=""))
    
    def insert_content(self, content_callback):
        """
        Fügt Section-Content ein
        
        Args:
            content_callback: Callable das den Content einfügt
        """
        self.content_start = self.text_widget.index(tk.END)
        
        # Content-Callback ausführen
        content_callback()
        
        self.content_end = self.text_widget.index(tk.END)
        
        # Content-Tag hinzufügen
        self.text_widget.tag_add(self.content_tag, self.content_start, self.content_end)
        
        # Initial State setzen
        if self.is_collapsed:
            self.text_widget.tag_configure(self.content_tag, elide=True)
        else:
            self.text_widget.tag_configure(self.content_tag, elide=False)
    
    def _toggle(self, event=None):
        """Toggle expand/collapse State"""
        if self._animation_in_progress:
            return "break"
        
        if self.is_collapsed:
            self._expand()
        else:
            self._collapse()
        
        return "break"
    
    def _expand(self):
        """Expandiert die Section (optional mit Animation)"""
        if self.animate and self.parent_window:
            self._animated_expand()
        else:
            self._instant_expand()
    
    def _collapse(self):
        """Collapsed die Section (optional mit Animation)"""
        if self.animate and self.parent_window:
            self._animated_collapse()
        else:
            self._instant_collapse()
    
    def _instant_expand(self):
        """Instant Expand ohne Animation"""
        self.is_collapsed = False
        self._update_arrow("▼")
        self.text_widget.tag_configure(self.content_tag, elide=False)
    
    def _instant_collapse(self):
        """Instant Collapse ohne Animation"""
        self.is_collapsed = True
        self._update_arrow("▶")
        self.text_widget.tag_configure(self.content_tag, elide=True)
    
    def _animated_expand(self):
        """Expandiert mit smooth Animation"""
        self._animation_in_progress = True
        self.is_collapsed = False
        self._update_arrow("▼")
        
        # Sofort einblenden (Animation könnte hier komplexer sein)
        self.text_widget.tag_configure(self.content_tag, elide=False)
        
        # Scroll zu Content
        if self.parent_window:
            self.parent_window.after(50, lambda: self.text_widget.see(self.content_start))
        
        self._animation_in_progress = False
    
    def _animated_collapse(self):
        """Collapsed mit smooth Animation"""
        self._animation_in_progress = True
        self.is_collapsed = True
        self._update_arrow("▶")
        
        # Sofort verstecken
        self.text_widget.tag_configure(self.content_tag, elide=True)
        
        self._animation_in_progress = False
    
    def _update_arrow(self, new_arrow: str):
        """Aktualisiert Arrow Icon"""
        try:
            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.delete(self.arrow_start, self.arrow_end)
            self.text_widget.insert(self.arrow_start, f"{new_arrow} ", self.arrow_tag)
            self.arrow_end = self.text_widget.index(f"{self.arrow_start} + 2c")
            self.text_widget.config(state=tk.DISABLED)
        except tk.TclError:
            pass  # Widget existiert nicht mehr
