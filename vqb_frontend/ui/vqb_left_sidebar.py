"""
VQB UI Components - Left Sidebar

OOP-based left sidebar with tabs for filters, search, and navigation.
"""

import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger(__name__)


class VQBLeftSidebar:
    """
    VQB Left Sidebar Component
    
    Provides tabbed interface for filters, search, and navigation.
    """
    
    def __init__(self, parent: tk.Frame, controller):
        """
        Initialize left sidebar
        
        Args:
            parent: Parent frame
            controller: Application controller
        """
        self.parent = parent
        self.controller = controller
        
        # Create sidebar frame
        self.sidebar = ttk.Frame(parent, width=250, relief=tk.RAISED, borderwidth=1)
        self.sidebar.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
        self.sidebar.pack_propagate(False)  # Maintain width
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.sidebar)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Create tabs
        self._create_filter_tab()
        self._create_search_tab()
        self._create_navigation_tab()
        
        logger.info("VQB Left Sidebar initialized")
    
    def _create_filter_tab(self):
        """Create filter tab"""
        filter_frame = ttk.Frame(self.notebook)
        self.notebook.add(filter_frame, text="📊 Filter")
        
        # Filter title
        ttk.Label(
            filter_frame,
            text="Multidimensionale Filter",
            font=("Arial", 10, "bold")
        ).pack(pady=5)
        
        # Temporal filter
        temporal_group = ttk.LabelFrame(filter_frame, text="⏰ Zeitlich")
        temporal_group.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(temporal_group, text="Von:").pack(anchor=tk.W, padx=5)
        self.date_from_entry = ttk.Entry(temporal_group, width=20)
        self.date_from_entry.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(temporal_group, text="Bis:").pack(anchor=tk.W, padx=5)
        self.date_to_entry = ttk.Entry(temporal_group, width=20)
        self.date_to_entry.pack(fill=tk.X, padx=5, pady=2)
        
        # Legal filter
        legal_group = ttk.LabelFrame(filter_frame, text="⚖️ Rechtlich")
        legal_group.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(legal_group, text="Rechtsbereich:").pack(anchor=tk.W, padx=5)
        self.legal_domain_combo = ttk.Combobox(
            legal_group,
            values=["Alle", "Umweltrecht", "Baurecht", "Verwaltungsrecht"],
            state="readonly",
            width=18
        )
        self.legal_domain_combo.current(0)
        self.legal_domain_combo.pack(fill=tk.X, padx=5, pady=2)
        
        # Geo filter
        geo_group = ttk.LabelFrame(filter_frame, text="🌍 Geografisch")
        geo_group.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(geo_group, text="Föderale Ebene:").pack(anchor=tk.W, padx=5)
        self.federal_level_combo = ttk.Combobox(
            geo_group,
            values=["Alle", "Bund", "Land", "Kommune"],
            state="readonly",
            width=18
        )
        self.federal_level_combo.current(0)
        self.federal_level_combo.pack(fill=tk.X, padx=5, pady=2)
        
        # Apply button
        ttk.Button(
            filter_frame,
            text="Filter anwenden",
            command=self.controller.apply_filters
        ).pack(pady=10)
        
        ttk.Button(
            filter_frame,
            text="Filter zurücksetzen",
            command=self.controller.clear_filters
        ).pack(pady=5)
    
    def _create_search_tab(self):
        """Create search tab"""
        search_frame = ttk.Frame(self.notebook)
        self.notebook.add(search_frame, text="🔍 Suche")
        
        # Search title
        ttk.Label(
            search_frame,
            text="Erweiterte Suche",
            font=("Arial", 10, "bold")
        ).pack(pady=5)
        
        # Search input
        ttk.Label(search_frame, text="Suchbegriff:").pack(anchor=tk.W, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=25)
        self.search_entry.pack(fill=tk.X, padx=5, pady=2)
        self.search_entry.bind("<Return>", lambda e: self.controller.execute_search())
        
        # Search type
        ttk.Label(search_frame, text="Suchtyp:").pack(anchor=tk.W, padx=5, pady=(10, 0))
        self.search_type_var = tk.StringVar(value="all")
        
        ttk.Radiobutton(
            search_frame,
            text="Alle Bereiche",
            variable=self.search_type_var,
            value="all"
        ).pack(anchor=tk.W, padx=15)
        
        ttk.Radiobutton(
            search_frame,
            text="Prozesse",
            variable=self.search_type_var,
            value="processes"
        ).pack(anchor=tk.W, padx=15)
        
        ttk.Radiobutton(
            search_frame,
            text="Dokumente",
            variable=self.search_type_var,
            value="documents"
        ).pack(anchor=tk.W, padx=15)
        
        ttk.Radiobutton(
            search_frame,
            text="Rechtsnormen",
            variable=self.search_type_var,
            value="norms"
        ).pack(anchor=tk.W, padx=15)
        
        # Search options
        self.semantic_search_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            search_frame,
            text="Semantische Suche (AI)",
            variable=self.semantic_search_var
        ).pack(anchor=tk.W, padx=5, pady=(10, 0))
        
        # Search button
        ttk.Button(
            search_frame,
            text="🔍 Suchen",
            command=self.controller.execute_search
        ).pack(pady=10)
        
        # Recent searches
        ttk.Label(
            search_frame,
            text="Letzte Suchen:",
            font=("Arial", 9, "bold")
        ).pack(anchor=tk.W, padx=5, pady=(10, 0))
        
        self.recent_searches_list = tk.Listbox(search_frame, height=5)
        self.recent_searches_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _create_navigation_tab(self):
        """Create navigation tab"""
        nav_frame = ttk.Frame(self.notebook)
        self.notebook.add(nav_frame, text="🗺️ Navigation")
        
        # Navigation title
        ttk.Label(
            nav_frame,
            text="Schnellnavigation",
            font=("Arial", 10, "bold")
        ).pack(pady=5)
        
        # Bookmarks
        bookmark_group = ttk.LabelFrame(nav_frame, text="⭐ Lesezeichen")
        bookmark_group.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.bookmarks_list = tk.Listbox(bookmark_group, height=6)
        self.bookmarks_list.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Add sample bookmarks
        for item in ["Häufige Genehmigungen", "Aktuelle Verfahren", "Compliance Dashboard"]:
            self.bookmarks_list.insert(tk.END, item)
        
        # Quick actions
        quick_group = ttk.LabelFrame(nav_frame, text="⚡ Schnellzugriff")
        quick_group.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            quick_group,
            text="Timeline anzeigen",
            command=lambda: self.controller.switch_content_tab("timeline")
        ).pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(
            quick_group,
            text="Prozesse anzeigen",
            command=lambda: self.controller.switch_content_tab("processes")
        ).pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(
            quick_group,
            text="Neue Abfrage",
            command=self.controller.new_query
        ).pack(fill=tk.X, padx=5, pady=2)
    
    def get_frame(self) -> ttk.Frame:
        """Get sidebar frame"""
        return self.sidebar
    
    def toggle_visibility(self):
        """Toggle sidebar visibility"""
        if self.sidebar.winfo_viewable():
            self.sidebar.pack_forget()
        else:
            self.sidebar.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
