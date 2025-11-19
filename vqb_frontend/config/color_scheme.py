"""
VQB Frontend - Color Scheme

Central color definitions for consistent theming.
"""


class ColorScheme:
    """Color scheme for VQB application"""
    
    # =========================================================================
    # Primary Colors
    # =========================================================================
    PRIMARY_BLUE = "#0066CC"
    PRIMARY_DARK = "#003366"
    PRIMARY_LIGHT = "#6699FF"
    ACCENT = "#FF6600"
    
    # =========================================================================
    # Status Colors (for Processes)
    # =========================================================================
    STATUS_PLANNED = "#FFA500"       # Orange - Geplant
    STATUS_IN_PROGRESS = "#4169E1"   # Royal Blue - In Bearbeitung
    STATUS_COMPLETED = "#32CD32"     # Lime Green - Abgeschlossen
    STATUS_BLOCKED = "#DC143C"       # Crimson - Blockiert
    STATUS_CANCELLED = "#808080"     # Gray - Abgebrochen
    
    # =========================================================================
    # Relationship Colors (for Graph Edges)
    # =========================================================================
    REL_GRAPH = "#9370DB"        # Medium Purple - Graph (Neo4j)
    REL_VECTOR = "#FF6347"       # Tomato - Vector (ChromaDB)
    REL_RELATIONAL = "#4682B4"   # Steel Blue - Relational (PostgreSQL)
    REL_FILE = "#DAA520"         # Goldenrod - File
    
    # =========================================================================
    # UI Element Colors
    # =========================================================================
    BACKGROUND = "#F5F5F5"       # White Smoke
    PANEL_BG = "#FFFFFF"         # White
    BORDER = "#CCCCCC"           # Light Gray
    HOVER = "#E6F2FF"            # Light Blue (hover effect)
    SELECTED = "#CCE5FF"         # Lighter Blue (selected item)
    
    # =========================================================================
    # Text Colors
    # =========================================================================
    TEXT_PRIMARY = "#333333"     # Dark Gray
    TEXT_SECONDARY = "#666666"   # Medium Gray
    TEXT_DISABLED = "#999999"    # Light Gray
    TEXT_ERROR = "#DC143C"       # Crimson
    TEXT_SUCCESS = "#32CD32"     # Lime Green
    TEXT_WARNING = "#FFA500"     # Orange
    
    # =========================================================================
    # Timeline-Specific Colors
    # =========================================================================
    TIMELINE_GRID = "#E0E0E0"        # Light Gray (grid lines)
    TIMELINE_TODAY = "#FF4500"       # Orange Red (today marker)
    TIMELINE_MILESTONE = "#FFD700"   # Gold (milestone marker)
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    @classmethod
    def get_status_color(cls, status: str) -> str:
        """
        Get color for process status
        
        Args:
            status: Status string (planned, in_progress, completed, blocked, cancelled)
        
        Returns:
            Hex color code
        """
        status_map = {
            "planned": cls.STATUS_PLANNED,
            "in_progress": cls.STATUS_IN_PROGRESS,
            "completed": cls.STATUS_COMPLETED,
            "blocked": cls.STATUS_BLOCKED,
            "cancelled": cls.STATUS_CANCELLED,
        }
        return status_map.get(status.lower(), cls.PRIMARY_BLUE)
    
    @classmethod
    def get_relationship_color(cls, rel_type: str) -> str:
        """
        Get color for relationship type
        
        Args:
            rel_type: Relationship type (graph, vector, relational, file)
        
        Returns:
            Hex color code
        """
        rel_map = {
            "graph": cls.REL_GRAPH,
            "vector": cls.REL_VECTOR,
            "relational": cls.REL_RELATIONAL,
            "file": cls.REL_FILE,
        }
        return rel_map.get(rel_type.lower(), cls.PRIMARY_BLUE)
    
    @classmethod
    def lighten_color(cls, hex_color: str, factor: float = 0.2) -> str:
        """
        Lighten a hex color by a factor
        
        Args:
            hex_color: Hex color code (e.g., "#0066CC")
            factor: Lightening factor (0.0 to 1.0)
        
        Returns:
            Lightened hex color code
        """
        # Remove '#' if present
        hex_color = hex_color.lstrip('#')
        
        # Convert to RGB
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        
        # Lighten
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
