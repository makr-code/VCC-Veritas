"""
VQB UI Components - Right Sidebar

OOP-based right sidebar with tabs for details, properties, and AI suggestions.
"""

import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger(__name__)


class VQBRightSidebar:
    """
    VQB Right Sidebar Component
    
    Provides tabbed interface for details, properties, and AI suggestions.
    """
    
    def __init__(self, parent: tk.Frame, controller):
        """
        Initialize right sidebar
        
        Args:
            parent: Parent frame
            controller: Application controller
        """
        self.parent = parent
        self.controller = controller
        
        # Create sidebar frame
        self.sidebar = ttk.Frame(parent, width=300, relief=tk.RAISED, borderwidth=1)
        self.sidebar.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        self.sidebar.pack_propagate(False)  # Maintain width
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.sidebar)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Create tabs
        self._create_details_tab()
        self._create_properties_tab()
        self._create_ai_suggestions_tab()
        
        logger.info("VQB Right Sidebar initialized")
    
    def _create_details_tab(self):
        """Create details tab"""
        details_frame = ttk.Frame(self.notebook)
        self.notebook.add(details_frame, text="ℹ️ Details")
        
        # Details title
        ttk.Label(
            details_frame,
            text="Entitäts-Details",
            font=("Arial", 10, "bold")
        ).pack(pady=5)
        
        # Details text widget
        details_scroll = ttk.Scrollbar(details_frame)
        details_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.details_text = tk.Text(
            details_frame,
            wrap=tk.WORD,
            yscrollcommand=details_scroll.set,
            height=20
        )
        self.details_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        details_scroll.config(command=self.details_text.yview)
        
        # Placeholder text
        self.details_text.insert(
            1.0,
            "Wählen Sie eine Entität aus, um Details anzuzeigen.\n\n"
            "Verfügbare Informationen:\n"
            "• URN\n"
            "• Titel und Beschreibung\n"
            "• Zeitliche Zuordnung\n"
            "• Rechtliche Grundlagen\n"
            "• Zugeordnete Dokumente\n"
            "• Verantwortliche Stelle"
        )
        self.details_text.config(state=tk.DISABLED)
    
    def _create_properties_tab(self):
        """Create properties tab"""
        props_frame = ttk.Frame(self.notebook)
        self.notebook.add(props_frame, text="📋 Eigenschaften")
        
        # Properties title
        ttk.Label(
            props_frame,
            text="Eigenschaften",
            font=("Arial", 10, "bold")
        ).pack(pady=5)
        
        # Properties treeview
        props_tree_frame = ttk.Frame(props_frame)
        props_tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        props_scroll = ttk.Scrollbar(props_tree_frame)
        props_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.properties_tree = ttk.Treeview(
            props_tree_frame,
            columns=("value",),
            yscrollcommand=props_scroll.set,
            show="tree"
        )
        self.properties_tree.pack(fill=tk.BOTH, expand=True)
        props_scroll.config(command=self.properties_tree.yview)
        
        # Sample properties
        self.properties_tree.insert("", tk.END, text="ID", values=("---",))
        self.properties_tree.insert("", tk.END, text="Typ", values=("---",))
        self.properties_tree.insert("", tk.END, text="Status", values=("---",))
        self.properties_tree.insert("", tk.END, text="Erstellt", values=("---",))
        self.properties_tree.insert("", tk.END, text="Geändert", values=("---",))
    
    def _create_ai_suggestions_tab(self):
        """Create AI suggestions tab"""
        ai_frame = ttk.Frame(self.notebook)
        self.notebook.add(ai_frame, text="🤖 AI Vorschläge")
        
        # AI suggestions title
        ttk.Label(
            ai_frame,
            text="KI-Empfehlungen",
            font=("Arial", 10, "bold")
        ).pack(pady=5)
        
        # Suggestions info
        ttk.Label(
            ai_frame,
            text="Basierend auf Ihrem Kontext:",
            font=("Arial", 9, "italic")
        ).pack(anchor=tk.W, padx=5)
        
        # Suggestions list
        suggest_group = ttk.LabelFrame(ai_frame, text="💡 Vorschläge")
        suggest_group.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.suggestions_list = tk.Listbox(suggest_group, height=10)
        self.suggestions_list.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Sample suggestions
        sample_suggestions = [
            "Ähnliche Verfahren aus 2023",
            "Relevante Rechtsnormen",
            "Verwandte Dokumente",
            "Compliance-Hinweise",
            "Frist-Warnungen"
        ]
        for suggestion in sample_suggestions:
            self.suggestions_list.insert(tk.END, f"• {suggestion}")
        
        # Action buttons
        button_frame = ttk.Frame(ai_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            button_frame,
            text="Details anzeigen",
            command=self._show_suggestion_details
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            button_frame,
            text="Vorschläge aktualisieren",
            command=self.controller.refresh_ai_suggestions
        ).pack(fill=tk.X, pady=2)
    
    def _show_suggestion_details(self):
        """Show details of selected suggestion"""
        selection = self.suggestions_list.curselection()
        if selection:
            item = self.suggestions_list.get(selection[0])
            logger.info(f"Selected suggestion: {item}")
            self.controller.show_suggestion_details(item)
    
    def update_details(self, entity_data: dict):
        """Update details display"""
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        
        # Format entity data
        details = f"URN: {entity_data.get('urn', 'N/A')}\n\n"
        details += f"Titel: {entity_data.get('title', 'N/A')}\n\n"
        details += f"Typ: {entity_data.get('type', 'N/A')}\n\n"
        details += f"Status: {entity_data.get('status', 'N/A')}\n\n"
        details += f"Beschreibung:\n{entity_data.get('description', 'Keine Beschreibung verfügbar')}\n"
        
        self.details_text.insert(1.0, details)
        self.details_text.config(state=tk.DISABLED)
    
    def update_properties(self, entity_data: dict):
        """Update properties display"""
        # Clear existing
        for item in self.properties_tree.get_children():
            self.properties_tree.delete(item)
        
        # Add new properties
        for key, value in entity_data.items():
            if key not in ["description"]:  # Skip long fields
                self.properties_tree.insert("", tk.END, text=key, values=(str(value),))
    
    def get_frame(self) -> ttk.Frame:
        """Get sidebar frame"""
        return self.sidebar
    
    def toggle_visibility(self):
        """Toggle sidebar visibility"""
        if self.sidebar.winfo_viewable():
            self.sidebar.pack_forget()
        else:
            self.sidebar.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
