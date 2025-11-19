"""
VQB UI Components - Menu Bar

OOP-based menu bar component for VQB application.
"""

import tkinter as tk
from tkinter import messagebox
from typing import Callable, Optional
import logging

logger = logging.getLogger(__name__)


class VQBMenuBar:
    """
    VQB Menu Bar Component
    
    Provides structured menu with File, Edit, View, Tools, and Help menus.
    Follows OOP principles with clean separation of concerns.
    """
    
    def __init__(self, parent: tk.Tk, controller):
        """
        Initialize menu bar
        
        Args:
            parent: Parent window
            controller: Application controller for callbacks
        """
        self.parent = parent
        self.controller = controller
        
        # Create menu bar
        self.menubar = tk.Menu(parent)
        parent.config(menu=self.menubar)
        
        # Build menus
        self._create_file_menu()
        self._create_edit_menu()
        self._create_view_menu()
        self._create_tools_menu()
        self._create_help_menu()
        
        logger.info("VQB Menu Bar initialized")
    
    def _create_file_menu(self):
        """Create File menu"""
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Datei", menu=file_menu)
        
        file_menu.add_command(
            label="Neue Abfrage...",
            accelerator="Ctrl+N",
            command=self.controller.new_query
        )
        file_menu.add_command(
            label="Abfrage öffnen...",
            accelerator="Ctrl+O",
            command=self.controller.open_query
        )
        file_menu.add_command(
            label="Abfrage speichern",
            accelerator="Ctrl+S",
            command=self.controller.save_query
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Daten laden...",
            command=self.controller.load_data
        )
        file_menu.add_command(
            label="Export...",
            command=self.controller.export_data
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Einstellungen...",
            command=self.controller.show_settings
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Beenden",
            accelerator="Ctrl+Q",
            command=self.controller.quit_application
        )
    
    def _create_edit_menu(self):
        """Create Edit menu"""
        edit_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Bearbeiten", menu=edit_menu)
        
        edit_menu.add_command(
            label="Rückgängig",
            accelerator="Ctrl+Z",
            command=self.controller.undo
        )
        edit_menu.add_command(
            label="Wiederherstellen",
            accelerator="Ctrl+Y",
            command=self.controller.redo
        )
        edit_menu.add_separator()
        edit_menu.add_command(
            label="Kopieren",
            accelerator="Ctrl+C",
            command=self.controller.copy
        )
        edit_menu.add_command(
            label="Einfügen",
            accelerator="Ctrl+V",
            command=self.controller.paste
        )
        edit_menu.add_separator()
        edit_menu.add_command(
            label="Filter löschen",
            command=self.controller.clear_filters
        )
    
    def _create_view_menu(self):
        """Create View menu"""
        view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Ansicht", menu=view_menu)
        
        # Content tabs
        view_menu.add_command(
            label="Timeline",
            accelerator="Ctrl+1",
            command=lambda: self.controller.switch_content_tab("timeline")
        )
        view_menu.add_command(
            label="Prozesse",
            accelerator="Ctrl+2",
            command=lambda: self.controller.switch_content_tab("processes")
        )
        view_menu.add_separator()
        
        # Sidebars
        view_menu.add_checkbutton(
            label="Linke Sidebar",
            command=self.controller.toggle_left_sidebar
        )
        view_menu.add_checkbutton(
            label="Rechte Sidebar",
            command=self.controller.toggle_right_sidebar
        )
        view_menu.add_checkbutton(
            label="AI Chat",
            command=self.controller.toggle_ai_chat
        )
        view_menu.add_separator()
        
        # Zoom
        view_menu.add_command(
            label="Vergrößern",
            accelerator="Ctrl++",
            command=self.controller.zoom_in
        )
        view_menu.add_command(
            label="Verkleinern",
            accelerator="Ctrl+-",
            command=self.controller.zoom_out
        )
        view_menu.add_command(
            label="Zoom zurücksetzen",
            accelerator="Ctrl+0",
            command=self.controller.zoom_reset
        )
    
    def _create_tools_menu(self):
        """Create Tools menu"""
        tools_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Tools", menu=tools_menu)
        
        tools_menu.add_command(
            label="Multidimensionale Suche...",
            command=self.controller.show_multidimensional_search
        )
        tools_menu.add_command(
            label="URN Resolver...",
            command=self.controller.show_urn_resolver
        )
        tools_menu.add_separator()
        tools_menu.add_command(
            label="Compliance Check...",
            command=self.controller.run_compliance_check
        )
        tools_menu.add_command(
            label="Impact Analyse...",
            command=self.controller.run_impact_analysis
        )
        tools_menu.add_separator()
        tools_menu.add_command(
            label="Bericht generieren...",
            command=self.controller.generate_report
        )
    
    def _create_help_menu(self):
        """Create Help menu"""
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Hilfe", menu=help_menu)
        
        help_menu.add_command(
            label="Dokumentation",
            accelerator="F1",
            command=self.controller.show_documentation
        )
        help_menu.add_command(
            label="Tastenkombinationen",
            command=self.controller.show_shortcuts
        )
        help_menu.add_separator()
        help_menu.add_command(
            label="VCC-URN Info...",
            command=self.controller.show_urn_info
        )
        help_menu.add_separator()
        help_menu.add_command(
            label="Über VQB...",
            command=self.controller.show_about
        )
