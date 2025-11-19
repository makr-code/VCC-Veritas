"""
VQB Frontend - Main Application

Visual Query Builder for VCC-Veritas with complete OOP-based UI structure.

Layout:
- MenuBar (top)
- Toolbar (below menubar)
- Left Sidebar with tabs (Filter, Search, Navigation)
- Content Area with tabs (Timeline, Processes)
- Right Sidebar with tabs (Details, Properties, AI Suggestions)
- AI Chat Panel (bottom)
- StatusBar (bottom)
"""

import tkinter as tk
from tkinter import ttk
import logging
import sys

from vqb_frontend.config.app_config import config
from vqb_frontend.config.color_scheme import ColorScheme
from vqb_frontend.models.process_model import ProcessModel
from vqb_frontend.models.document_model import DocumentModel
from vqb_frontend.services.async_worker import get_async_worker
from vqb_frontend.controller import VQBController

# UI Components
from vqb_frontend.ui.vqb_menubar import VQBMenuBar
from vqb_frontend.ui.vqb_toolbar import VQBToolbar
from vqb_frontend.ui.vqb_statusbar import VQBStatusBar
from vqb_frontend.ui.vqb_left_sidebar import VQBLeftSidebar
from vqb_frontend.ui.vqb_right_sidebar import VQBRightSidebar
from vqb_frontend.ui.vqb_content_area import VQBContentArea
from vqb_frontend.ui.vqb_ai_chat import VQBAIChatPanel

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
    
    Complete OOP-based UI structure following VPB CI pattern:
    - MenuBar, Toolbar, StatusBar
    - Left Sidebar (tabs: Filter, Search, Navigation)
    - Content Area (tabs: Timeline, Processes)  
    - Right Sidebar (tabs: Details, Properties, AI Suggestions)
    - AI Chat Panel (bottom)
    """
    
    def __init__(self):
        """Initialize VQB application"""
        super().__init__()
        
        logger.info(f"Starting {config.APP_NAME} v{config.APP_VERSION}")
        
        # Window configuration
        self.title(f"{config.APP_NAME} v{config.APP_VERSION}")
        self.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        self.minsize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)
        
        # Configure style
        self._configure_style()
        
        # Initialize models
        self.process_model = ProcessModel()
        self.document_model = DocumentModel()
        
        # Initialize async worker
        self.async_worker = get_async_worker(num_threads=config.ASYNC_WORKER_THREADS)
        
        # Initialize controller
        self.controller = VQBController(self)
        
        # Create UI components (OOP-based)
        self._create_ui()
        
        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()
        
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
        style.configure('TNotebook', background=ColorScheme.BACKGROUND)
    
    def _create_ui(self):
        """Create main UI layout with all OOP components"""
        # 1. Menu Bar (top)
        self.menubar = VQBMenuBar(self, self.controller)
        self.controller.menubar = self.menubar
        
        # 2. Toolbar (below menubar)
        toolbar_container = ttk.Frame(self)
        toolbar_container.pack(side=tk.TOP, fill=tk.X)
        self.toolbar = VQBToolbar(toolbar_container, self.controller)
        self.controller.toolbar = self.toolbar
        
        # 3. Main container for sidebars and content
        main_container = ttk.Frame(self)
        main_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # 4. Left Sidebar (left side)
        self.left_sidebar = VQBLeftSidebar(main_container, self.controller)
        self.controller.left_sidebar = self.left_sidebar
        
        # 5. Content Area (center) with tabs: Timeline, Processes
        self.content_area = VQBContentArea(main_container, self.controller)
        self.controller.content_area = self.content_area
        
        # 6. Right Sidebar (right side)
        self.right_sidebar = VQBRightSidebar(main_container, self.controller)
        self.controller.right_sidebar = self.right_sidebar
        
        # 7. AI Chat Panel (bottom, above statusbar)
        ai_chat_container = ttk.Frame(self)
        ai_chat_container.pack(side=tk.BOTTOM, fill=tk.BOTH, before=main_container)
        self.ai_chat = VQBAIChatPanel(ai_chat_container, self.controller)
        self.controller.ai_chat = self.ai_chat
        
        # 8. Status Bar (very bottom)
        statusbar_container = ttk.Frame(self)
        statusbar_container.pack(side=tk.BOTTOM, fill=tk.X)
        self.statusbar = VQBStatusBar(statusbar_container, self.controller)
        self.controller.statusbar = self.statusbar
        
        # Set initial status
        self.statusbar.set_status("Bereit - VQB initialisiert")
        self.statusbar.set_connection_status(True)
        self.statusbar.update_statistics(0, 0)
        
        logger.info("UI components created successfully")
    
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        # File operations
        self.bind("<Control-n>", lambda e: self.controller.new_query())
        self.bind("<Control-o>", lambda e: self.controller.open_query())
        self.bind("<Control-s>", lambda e: self.controller.save_query())
        self.bind("<Control-q>", lambda e: self.controller.quit_application())
        
        # Edit operations
        self.bind("<Control-z>", lambda e: self.controller.undo())
        self.bind("<Control-y>", lambda e: self.controller.redo())
        
        # View operations
        self.bind("<Control-1>", lambda e: self.controller.switch_content_tab("timeline"))
        self.bind("<Control-2>", lambda e: self.controller.switch_content_tab("processes"))
        self.bind("<Control-plus>", lambda e: self.controller.zoom_in())
        self.bind("<Control-minus>", lambda e: self.controller.zoom_out())
        self.bind("<Control-0>", lambda e: self.controller.zoom_reset())
        
        # Help
        self.bind("<F1>", lambda e: self.controller.show_documentation())
        
        logger.info("Keyboard shortcuts configured")
    
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
