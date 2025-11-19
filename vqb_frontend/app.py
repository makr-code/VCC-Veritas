"""
VQB Frontend - Main Application

Visual Query Builder for VCC-Veritas
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import sys

from vqb_frontend.config.app_config import config
from vqb_frontend.config.color_scheme import ColorScheme
from vqb_frontend.models.process_model import ProcessModel
from vqb_frontend.models.document_model import DocumentModel
from vqb_frontend.services.async_worker import get_async_worker

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if config.DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vqb_frontend.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class VQBApplication(tk.Tk):
    """
    Main VQB Application Window
    
    This is a minimal implementation demonstrating the architecture.
    Full implementation will include Timeline, Graph, and Filter panels.
    """
    
    def __init__(self):
        """Initialize VQB application"""
        super().__init__()
        
        logger.info(f"Starting {config.APP_NAME} v{config.APP_VERSION}")
        
        # Window configuration
        self.title(config.APP_NAME)
        self.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        self.minsize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)
        
        # Configure style
        self._configure_style()
        
        # Initialize models
        self.process_model = ProcessModel()
        self.document_model = DocumentModel()
        
        # Initialize async worker
        self.async_worker = get_async_worker(num_threads=config.ASYNC_WORKER_THREADS)
        
        # Create UI
        self._create_menu()
        self._create_ui()
        
        # Start async result processing
        self._process_async_results()
        
        # Protocol for window close
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        logger.info("VQB Application initialized successfully")
    
    def _configure_style(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')  # Modern theme
        
        # Configure colors
        style.configure('TFrame', background=ColorScheme.BACKGROUND)
        style.configure('TLabel', background=ColorScheme.PANEL_BG, 
                       foreground=ColorScheme.TEXT_PRIMARY)
        style.configure('TButton', background=ColorScheme.PRIMARY_BLUE,
                       foreground='white')
    
    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Processes...", command=self._on_load_processes)
        file_menu.add_command(label="Load Documents...", command=self._on_load_documents)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Timeline", command=lambda: self._show_view("timeline"))
        view_menu.add_command(label="Graph", command=lambda: self._show_view("graph"))
        view_menu.add_command(label="Documents", command=lambda: self._show_view("documents"))
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _create_ui(self):
        """Create main UI layout"""
        # Configure grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Status bar (top)
        self.status_frame = ttk.Frame(self)
        self.status_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        self.status_label = ttk.Label(self.status_frame, 
                                     text="Welcome to VQB - Visual Query Builder")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Info labels
        self.info_frame = ttk.Frame(self.status_frame)
        self.info_frame.pack(side=tk.RIGHT, padx=5)
        
        self.process_count_label = ttk.Label(self.info_frame, text="Processes: 0")
        self.process_count_label.pack(side=tk.LEFT, padx=5)
        
        self.doc_count_label = ttk.Label(self.info_frame, text="Documents: 0")
        self.doc_count_label.pack(side=tk.LEFT, padx=5)
        
        # Main content area
        self.content_frame = ttk.Frame(self, style='TFrame')
        self.content_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        # Placeholder text
        welcome_label = ttk.Label(
            self.content_frame,
            text=f"{config.APP_NAME}\n\nVersion {config.APP_VERSION}\n\n"
                 f"This is a concept implementation.\n"
                 f"Full features include:\n"
                 f"• Timeline View (Gantt-style)\n"
                 f"• Document Graph Visualization\n"
                 f"• AI-assisted Filtering\n"
                 f"• VPB Process Integration\n"
                 f"• UDS3 Multi-Database Support",
            justify=tk.CENTER,
            font=('Arial', 12)
        )
        welcome_label.pack(expand=True)
        
        # Bottom status bar
        self.bottom_status = ttk.Label(self, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.bottom_status.grid(row=2, column=0, columnspan=2, sticky="ew")
    
    def _process_async_results(self):
        """
        Process async task results
        
        Called periodically to handle callbacks from background tasks.
        """
        try:
            self.async_worker.process_results()
        except Exception as e:
            logger.error(f"Error processing async results: {e}", exc_info=True)
        
        # Schedule next check
        self.after(100, self._process_async_results)
    
    def _update_status(self):
        """Update status bar with current counts"""
        process_count = self.process_model.get_count()
        doc_count = self.document_model.get_count()
        
        self.process_count_label.config(text=f"Processes: {process_count}")
        self.doc_count_label.config(text=f"Documents: {doc_count}")
    
    def _on_load_processes(self):
        """Handle load processes action"""
        messagebox.showinfo("Load Processes", 
                           "Process loading will be implemented in Phase 2.\n"
                           "Will connect to VPB backend API.")
    
    def _on_load_documents(self):
        """Handle load documents action"""
        messagebox.showinfo("Load Documents",
                           "Document loading will be implemented in Phase 3.\n"
                           "Will connect to UDS3 backend.")
    
    def _show_view(self, view_name: str):
        """Handle view switching"""
        messagebox.showinfo(f"{view_name.title()} View",
                           f"{view_name.title()} view will be implemented in later phases.")
    
    def _show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About VQB",
            f"{config.APP_NAME}\n"
            f"Version {config.APP_VERSION}\n\n"
            f"Visual Query Builder for VCC-Veritas\n"
            f"Connects VPB processes with documents\n\n"
            f"© 2025 VCC-Veritas Development Team"
        )
    
    def _on_closing(self):
        """Handle window close"""
        logger.info("Application closing...")
        
        # Shutdown async worker
        self.async_worker.shutdown()
        
        # Destroy window
        self.destroy()


def main():
    """Main entry point"""
    try:
        app = VQBApplication()
        app.mainloop()
    except Exception as e:
        logger.critical(f"Application crashed: {e}", exc_info=True)
        messagebox.showerror("Fatal Error", f"Application crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
