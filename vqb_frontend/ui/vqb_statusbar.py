"""
VQB UI Components - Status Bar

OOP-based status bar component for VQB application.
"""

import tkinter as tk
from tkinter import ttk
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class VQBStatusBar:
    """
    VQB Status Bar Component
    
    Displays application status, connection info, and statistics.
    """
    
    def __init__(self, parent: tk.Frame, controller):
        """
        Initialize status bar
        
        Args:
            parent: Parent frame
            controller: Application controller
        """
        self.parent = parent
        self.controller = controller
        
        # Create status bar frame
        self.statusbar = ttk.Frame(parent, relief=tk.SUNKEN, borderwidth=1)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status sections
        self._create_sections()
        
        logger.info("VQB Status Bar initialized")
    
    def _create_sections(self):
        """Create status bar sections"""
        # Left section - main status message
        self.status_label = ttk.Label(
            self.statusbar,
            text="Bereit",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # Center-right section - connection status
        self.connection_label = ttk.Label(
            self.statusbar,
            text="🔌 Verbunden",
            relief=tk.SUNKEN,
            width=15
        )
        self.connection_label.pack(side=tk.LEFT, padx=2)
        
        # Right section - statistics
        self.stats_label = ttk.Label(
            self.statusbar,
            text="Prozesse: 0 | Dokumente: 0",
            relief=tk.SUNKEN,
            width=30
        )
        self.stats_label.pack(side=tk.LEFT, padx=2)
        
        # Far right - time
        self.time_label = ttk.Label(
            self.statusbar,
            text="",
            relief=tk.SUNKEN,
            width=20
        )
        self.time_label.pack(side=tk.LEFT, padx=2)
        
        # Update time
        self._update_time()
    
    def _update_time(self):
        """Update time display"""
        now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        self.time_label.config(text=now)
        
        # Schedule next update
        self.parent.after(1000, self._update_time)
    
    def set_status(self, message: str):
        """Set status message"""
        self.status_label.config(text=message)
        logger.debug(f"Status: {message}")
    
    def set_connection_status(self, connected: bool):
        """Set connection status"""
        if connected:
            self.connection_label.config(text="🔌 Verbunden", foreground="green")
        else:
            self.connection_label.config(text="❌ Getrennt", foreground="red")
    
    def update_statistics(self, processes: int, documents: int):
        """Update statistics display"""
        self.stats_label.config(
            text=f"Prozesse: {processes} | Dokumente: {documents}"
        )
    
    def get_frame(self) -> ttk.Frame:
        """Get status bar frame"""
        return self.statusbar
