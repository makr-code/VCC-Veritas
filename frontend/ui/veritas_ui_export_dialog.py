#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS UI Module: Export Dialog
Dialog für Chat-Export (Word/Excel)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from typing import Optional, Callable, List, Dict
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class ExportDialog:
    """
    Export-Dialog für Chat-Konversationen
    
    Features:
    - Format-Auswahl (Word/Excel)
    - Zeitraum-Filter
    - Optionen (Metadata, Sources)
    - Auto-Filename
    """
    
    def __init__(
        self,
        parent: tk.Tk,
        on_export: Callable[[Dict], None],
        supported_formats: List[str] = ['.docx', '.xlsx']
    ):
        """
        Initialisiert Export-Dialog
        
        Args:
            parent: Parent Window
            on_export: Callback bei Export (receives config dict)
            supported_formats: Liste unterstützter Formate
        """
        self.parent = parent
        self.on_export = on_export
        self.supported_formats = supported_formats
        
        # Dialog Window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("📤 Chat exportieren")
        self.dialog.geometry("500x450")
        self.dialog.resizable(False, False)
        
        # Center on parent
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Variables
        self.format_var = tk.StringVar(value=supported_formats[0] if supported_formats else '.docx')
        self.period_var = tk.StringVar(value='all')
        self.include_metadata_var = tk.BooleanVar(value=True)
        self.include_sources_var = tk.BooleanVar(value=True)
        self.custom_filename_var = tk.StringVar(value='')
        
        # Build UI
        self._build_ui()
        
        logger.info("✅ Export-Dialog geöffnet")
    
    def _build_ui(self):
        """Erstellt UI-Komponenten"""
        # Title
        title_frame = tk.Frame(self.dialog, bg='#4472C4', height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="📤 Chat-Export",
            font=('Segoe UI', 16, 'bold'),
            fg='white',
            bg='#4472C4'
        )
        title_label.pack(pady=15)
        
        # Content Frame
        content_frame = tk.Frame(self.dialog, padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 1. Format Selection
        format_frame = tk.LabelFrame(
            content_frame,
            text="📄 Dateiformat",
            font=('Segoe UI', 10, 'bold'),
            padx=10,
            pady=10
        )
        format_frame.pack(fill=tk.X, pady=(0, 10))
        
        for fmt in self.supported_formats:
            icon = "📝" if fmt == '.docx' else "📊"
            label = f"{icon} {fmt.upper()} - "
            label += "Word-Dokument" if fmt == '.docx' else "Excel-Arbeitsmappe"
            
            rb = tk.Radiobutton(
                format_frame,
                text=label,
                variable=self.format_var,
                value=fmt,
                font=('Segoe UI', 9)
            )
            rb.pack(anchor=tk.W, pady=2)
        
        # 2. Time Period
        period_frame = tk.LabelFrame(
            content_frame,
            text="⏰ Zeitraum",
            font=('Segoe UI', 10, 'bold'),
            padx=10,
            pady=10
        )
        period_frame.pack(fill=tk.X, pady=(0, 10))
        
        periods = [
            ('all', 'Alle Messages'),
            ('today', 'Nur heute'),
            ('7days', 'Letzte 7 Tage'),
            ('30days', 'Letzte 30 Tage'),
            ('90days', 'Letzte 90 Tage')
        ]
        
        for value, label in periods:
            rb = tk.Radiobutton(
                period_frame,
                text=label,
                variable=self.period_var,
                value=value,
                font=('Segoe UI', 9)
            )
            rb.pack(anchor=tk.W, pady=2)
        
        # 3. Options
        options_frame = tk.LabelFrame(
            content_frame,
            text="⚙️ Optionen",
            font=('Segoe UI', 10, 'bold'),
            padx=10,
            pady=10
        )
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        cb_metadata = tk.Checkbutton(
            options_frame,
            text="📊 Metriken einschließen (Confidence, Dauer, Quellen)",
            variable=self.include_metadata_var,
            font=('Segoe UI', 9)
        )
        cb_metadata.pack(anchor=tk.W, pady=2)
        
        cb_sources = tk.Checkbutton(
            options_frame,
            text="📚 Quellenverzeichnis einschließen",
            variable=self.include_sources_var,
            font=('Segoe UI', 9)
        )
        cb_sources.pack(anchor=tk.W, pady=2)
        
        # 4. Filename (optional)
        filename_frame = tk.LabelFrame(
            content_frame,
            text="📝 Dateiname (optional)",
            font=('Segoe UI', 10, 'bold'),
            padx=10,
            pady=10
        )
        filename_frame.pack(fill=tk.X, pady=(0, 10))
        
        filename_entry = tk.Entry(
            filename_frame,
            textvariable=self.custom_filename_var,
            font=('Segoe UI', 9)
        )
        filename_entry.pack(fill=tk.X, pady=2)
        
        hint_label = tk.Label(
            filename_frame,
            text="Leer lassen für Auto-Generierung (z.B. veritas_chat_20251009_142315)",
            font=('Segoe UI', 8),
            fg='#666'
        )
        hint_label.pack(anchor=tk.W)
        
        # Buttons
        button_frame = tk.Frame(self.dialog, padx=20, pady=10)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        export_btn = tk.Button(
            button_frame,
            text="📤 Exportieren",
            command=self._on_export_click,
            font=('Segoe UI', 10, 'bold'),
            bg='#4CAF50',
            fg='white',
            padx=20,
            pady=8,
            cursor='hand2'
        )
        export_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        cancel_btn = tk.Button(
            button_frame,
            text="❌ Abbrechen",
            command=self._on_cancel_click,
            font=('Segoe UI', 10),
            padx=20,
            pady=8,
            cursor='hand2'
        )
        cancel_btn.pack(side=tk.RIGHT)
    
    def _on_export_click(self):
        """Export-Button geklickt"""
        # Build config
        config = {
            'format': self.format_var.get(),
            'period': self.period_var.get(),
            'include_metadata': self.include_metadata_var.get(),
            'include_sources': self.include_sources_var.get(),
            'filename': self.custom_filename_var.get().strip() or None
        }
        
        logger.info(f"📤 Export gestartet: {config}")
        
        # Close dialog
        self.dialog.destroy()
        
        # Call callback
        try:
            self.on_export(config)
        except Exception as e:
            logger.error(f"❌ Export fehlgeschlagen: {e}")
            messagebox.showerror(
                "Export-Fehler",
                f"Fehler beim Export:\n{str(e)}"
            )
    
    def _on_cancel_click(self):
        """Cancel-Button geklickt"""
        logger.info("❌ Export abgebrochen")
        self.dialog.destroy()
    
    def show(self):
        """Zeigt Dialog modal"""
        self.dialog.wait_window()


# ===== CONVENIENCE FUNCTION =====

def show_export_dialog(
    parent: tk.Tk,
    on_export: Callable[[Dict], None],
    supported_formats: Optional[List[str]] = None
) -> None:
    """
    Zeigt Export-Dialog
    
    Args:
        parent: Parent Window
        on_export: Callback bei Export
        supported_formats: Liste unterstützter Formate (optional)
    
    Example:
        >>> def handle_export(config):
        ...     print(f"Exportiere mit Config: {config}")
        >>> 
        >>> show_export_dialog(root, handle_export)
    """
    if supported_formats is None:
        supported_formats = ['.docx', '.xlsx']
    
    dialog = ExportDialog(parent, on_export, supported_formats)
    dialog.show()
