"""
VQB UI Components - Content Area

OOP-based content area with tabs for Timeline and Processes.
"""

import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger(__name__)


class VQBContentArea:
    """
    VQB Content Area Component
    
    Provides tabbed interface for Timeline and Processes views.
    """
    
    def __init__(self, parent: tk.Frame, controller):
        """
        Initialize content area
        
        Args:
            parent: Parent frame
            controller: Application controller
        """
        self.parent = parent
        self.controller = controller
        
        # Create content frame
        self.content_frame = ttk.Frame(parent)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Create notebook for content tabs
        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self._create_timeline_tab()
        self._create_processes_tab()
        
        # Bind tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        
        logger.info("VQB Content Area initialized")
    
    def _create_timeline_tab(self):
        """Create timeline tab"""
        timeline_frame = ttk.Frame(self.notebook)
        self.notebook.add(timeline_frame, text="📅 Timeline")
        
        # Timeline header
        header_frame = ttk.Frame(timeline_frame)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(
            header_frame,
            text="Prozess-Timeline (Gantt-Ansicht)",
            font=("Arial", 12, "bold")
        ).pack(side=tk.LEFT)
        
        # Timeline controls
        controls_frame = ttk.Frame(header_frame)
        controls_frame.pack(side=tk.RIGHT)
        
        ttk.Button(
            controls_frame,
            text="➖",
            width=3,
            command=self.controller.zoom_out
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            controls_frame,
            text="➕",
            width=3,
            command=self.controller.zoom_in
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            controls_frame,
            text="↻",
            width=3,
            command=self.controller.zoom_reset
        ).pack(side=tk.LEFT, padx=2)
        
        # Timeline canvas
        canvas_frame = ttk.Frame(timeline_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scroll = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Canvas for timeline
        self.timeline_canvas = tk.Canvas(
            canvas_frame,
            bg="#F5F5F5",
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set
        )
        self.timeline_canvas.pack(fill=tk.BOTH, expand=True)
        
        v_scroll.config(command=self.timeline_canvas.yview)
        h_scroll.config(command=self.timeline_canvas.xview)
        
        # Bind mouse events for pan and zoom
        self.timeline_canvas.bind("<ButtonPress-1>", self._on_canvas_press)
        self.timeline_canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.timeline_canvas.bind("<MouseWheel>", self._on_canvas_scroll)
        
        # Draw placeholder
        self._draw_timeline_placeholder()
    
    def _create_processes_tab(self):
        """Create processes tab"""
        processes_frame = ttk.Frame(self.notebook)
        self.notebook.add(processes_frame, text="📋 Prozesse")
        
        # Processes header
        header_frame = ttk.Frame(processes_frame)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(
            header_frame,
            text="Prozess-Übersicht",
            font=("Arial", 12, "bold")
        ).pack(side=tk.LEFT)
        
        # Search box
        ttk.Label(header_frame, text="Suche:").pack(side=tk.LEFT, padx=(20, 5))
        self.process_search = ttk.Entry(header_frame, width=30)
        self.process_search.pack(side=tk.LEFT)
        
        # Process list
        list_frame = ttk.Frame(processes_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scroll = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview for processes
        columns = ("URN", "Titel", "Status", "Start", "Ende", "Verantwortlich")
        self.processes_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="tree headings",
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set
        )
        
        # Configure columns
        self.processes_tree.heading("#0", text="ID")
        self.processes_tree.column("#0", width=50)
        
        for col in columns:
            self.processes_tree.heading(col, text=col)
            self.processes_tree.column(col, width=150)
        
        self.processes_tree.pack(fill=tk.BOTH, expand=True)
        
        v_scroll.config(command=self.processes_tree.yview)
        h_scroll.config(command=self.processes_tree.xview)
        
        # Bind selection event
        self.processes_tree.bind("<<TreeviewSelect>>", self._on_process_selected)
        
        # Add sample data
        self._add_sample_processes()
        
        # Context menu
        self._create_process_context_menu()
    
    def _draw_timeline_placeholder(self):
        """Draw placeholder for timeline"""
        # Clear canvas
        self.timeline_canvas.delete("all")
        
        # Draw placeholder text
        self.timeline_canvas.create_text(
            400, 300,
            text="Timeline-Ansicht\n\n"
                 "Hier werden Prozesse als Gantt-Diagramm dargestellt.\n\n"
                 "Features:\n"
                 "• Horizontale Zeitachse\n"
                 "• Prozesse als Balken\n"
                 "• Ereignisse als Marker\n"
                 "• Rechtliche Änderungen als vertikale Linien\n"
                 "• Zoom und Pan mit Maus\n\n"
                 "Implementierung in Phase 2",
            font=("Arial", 11),
            fill="#666666",
            justify=tk.CENTER
        )
        
        # Configure scroll region
        self.timeline_canvas.config(scrollregion=self.timeline_canvas.bbox("all"))
    
    def _add_sample_processes(self):
        """Add sample processes to tree"""
        sample_processes = [
            ("1", "urn:vcc:vpb:process:genehm-2024-001", 
             "Baugenehmigung Projekt Alpha", "In Bearbeitung", 
             "01.01.2024", "31.03.2024", "Stadt Potsdam"),
            ("2", "urn:vcc:vpb:process:genehm-2024-002",
             "Umweltgenehmigung Beta", "Genehmigt",
             "15.02.2024", "15.05.2024", "MLUK Brandenburg"),
            ("3", "urn:vcc:vpb:process:ueberwach-2024-001",
             "Wiederkehrende Überwachung", "Geplant",
             "01.06.2024", "30.06.2024", "Gewerbeaufsicht"),
        ]
        
        for item in sample_processes:
            self.processes_tree.insert("", tk.END, text=item[0], values=item[1:])
    
    def _create_process_context_menu(self):
        """Create context menu for process list"""
        self.process_menu = tk.Menu(self.processes_tree, tearoff=0)
        self.process_menu.add_command(
            label="Details anzeigen",
            command=self._show_process_details
        )
        self.process_menu.add_command(
            label="In Timeline anzeigen",
            command=self._show_in_timeline
        )
        self.process_menu.add_separator()
        self.process_menu.add_command(
            label="AI Zusammenfassung",
            command=self._ai_summarize_process
        )
        self.process_menu.add_command(
            label="Compliance prüfen",
            command=self._check_process_compliance
        )
        
        # Bind right-click
        self.processes_tree.bind("<Button-3>", self._show_context_menu)
    
    def _show_context_menu(self, event):
        """Show context menu"""
        # Select item under mouse
        item = self.processes_tree.identify_row(event.y)
        if item:
            self.processes_tree.selection_set(item)
            self.process_menu.post(event.x_root, event.y_root)
    
    def _on_process_selected(self, event):
        """Handle process selection"""
        selection = self.processes_tree.selection()
        if selection:
            item = self.processes_tree.item(selection[0])
            process_id = item["text"]
            process_data = {
                "id": process_id,
                "urn": item["values"][0],
                "title": item["values"][1],
                "status": item["values"][2],
                "start": item["values"][3],
                "end": item["values"][4],
                "responsible": item["values"][5]
            }
            self.controller.on_process_selected(process_data)
    
    def _show_process_details(self):
        """Show process details"""
        selection = self.processes_tree.selection()
        if selection:
            item = self.processes_tree.item(selection[0])
            logger.info(f"Show details for process: {item['values'][0]}")
            self.controller.show_process_details(item["values"][0])
    
    def _show_in_timeline(self):
        """Show process in timeline"""
        self.notebook.select(0)  # Switch to timeline tab
        # TODO: Scroll to and highlight process
    
    def _ai_summarize_process(self):
        """AI summarize selected process"""
        selection = self.processes_tree.selection()
        if selection:
            item = self.processes_tree.item(selection[0])
            self.controller.ai_summarize_entity(item["values"][0])
    
    def _check_process_compliance(self):
        """Check process compliance"""
        selection = self.processes_tree.selection()
        if selection:
            item = self.processes_tree.item(selection[0])
            self.controller.run_compliance_check(item["values"][0])
    
    def _on_canvas_press(self, event):
        """Handle canvas mouse press for panning"""
        self.timeline_canvas.scan_mark(event.x, event.y)
    
    def _on_canvas_drag(self, event):
        """Handle canvas drag for panning"""
        self.timeline_canvas.scan_dragto(event.x, event.y, gain=1)
    
    def _on_canvas_scroll(self, event):
        """Handle mouse wheel for zoom"""
        # Zoom in/out based on wheel direction
        if event.delta > 0:
            self.controller.zoom_in()
        else:
            self.controller.zoom_out()
    
    def _on_tab_changed(self, event):
        """Handle tab change"""
        current_tab = self.notebook.index(self.notebook.select())
        tab_names = ["timeline", "processes"]
        if current_tab < len(tab_names):
            logger.info(f"Switched to {tab_names[current_tab]} tab")
            self.controller.on_content_tab_changed(tab_names[current_tab])
    
    def switch_tab(self, tab_name: str):
        """Switch to specific tab"""
        tab_mapping = {
            "timeline": 0,
            "processes": 1
        }
        if tab_name in tab_mapping:
            self.notebook.select(tab_mapping[tab_name])
    
    def get_frame(self) -> ttk.Frame:
        """Get content frame"""
        return self.content_frame
