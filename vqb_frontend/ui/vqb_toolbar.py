"""
VQB UI Components - Toolbar

OOP-based toolbar component for VQB application.
"""

import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger(__name__)


class VQBToolbar:
    """
    VQB Toolbar Component
    
    Provides quick access buttons for common operations.
    """
    
    def __init__(self, parent: tk.Frame, controller):
        """
        Initialize toolbar
        
        Args:
            parent: Parent frame
            controller: Application controller
        """
        self.parent = parent
        self.controller = controller
        
        # Create toolbar frame
        self.toolbar = ttk.Frame(parent, relief=tk.RAISED, borderwidth=1)
        self.toolbar.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
        
        # Build toolbar buttons
        self._create_buttons()
        
        logger.info("VQB Toolbar initialized")
    
    def _create_buttons(self):
        """Create toolbar buttons"""
        # File operations
        ttk.Button(
            self.toolbar,
            text="📂 Öffnen",
            command=self.controller.open_query
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            self.toolbar,
            text="💾 Speichern",
            command=self.controller.save_query
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=5
        )
        
        # Query operations
        ttk.Button(
            self.toolbar,
            text="🔍 Suchen",
            command=self.controller.execute_search
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            self.toolbar,
            text="🔄 Aktualisieren",
            command=self.controller.refresh_data
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=5
        )
        
        # View operations
        ttk.Button(
            self.toolbar,
            text="📅 Timeline",
            command=lambda: self.controller.switch_content_tab("timeline")
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            self.toolbar,
            text="📋 Prozesse",
            command=lambda: self.controller.switch_content_tab("processes")
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=5
        )
        
        # AI operations
        ttk.Button(
            self.toolbar,
            text="🤖 AI Zusammenfassung",
            command=self.controller.ai_summarize
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            self.toolbar,
            text="✅ Compliance Check",
            command=self.controller.run_compliance_check
        ).pack(side=tk.LEFT, padx=2)
    
    def get_frame(self) -> ttk.Frame:
        """Get toolbar frame"""
        return self.toolbar
