#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS UI Module: Hybrid Search Metadata Display
==================================================

Visualisierung von Hybrid Search Ergebnissen:
- Score Deltas (Original vs. Reranked)
- Search Method Indicators (Vector/Graph/Relational)
- Ranking Strategy Tooltips
- Performance Metrics

Author: VERITAS Development Team
Date: 2025-01-28
Version: 1.0.0
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class HybridMetadataWidget(ttk.Frame):
    """
    Widget für Hybrid Search Metadata-Anzeige
    
    Features:
    - Score-Vergleich (Original vs. Reranked)
    - Score-Delta mit farbigem Indikator
    - Search-Method-Icons
    - Ranking-Strategy-Tooltip
    """
    
    def __init__(self, parent, source_data: Dict[str, Any], **kwargs):
        """
        Initialisiert das Metadata Widget
        
        Args:
            parent: Parent Widget
            source_data: Dict mit Hybrid Search Metadata
                {
                    "original_score": float,
                    "reranked_score": float,
                    "score_delta": float,
                    "search_methods": List[str],  # ["vector", "graph", "relational"]
                    "ranking_strategy": str,       # "rrf", "weighted", "borda"
                    "source_id": str,
                    "title": str
                }
        """
        super().__init__(parent, **kwargs)
        self.source_data = source_data
        self._create_widgets()
    
    def _create_widgets(self):
        """Erstellt alle UI-Komponenten"""
        # Container Frame
        container = ttk.Frame(self, style="HybridMeta.TFrame")
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # === ROW 1: Source Title ===
        title_frame = ttk.Frame(container)
        title_frame.pack(fill=tk.X, pady=(0, 5))
        
        title_label = ttk.Label(
            title_frame,
            text=self.source_data.get("title", "Unbekannte Quelle"),
            font=("Segoe UI", 10, "bold"),
            foreground="#2c3e50"
        )
        title_label.pack(side=tk.LEFT)
        
        # === ROW 2: Search Methods ===
        methods_frame = ttk.Frame(container)
        methods_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(
            methods_frame,
            text="Suchverfahren:",
            font=("Segoe UI", 9),
            foreground="#7f8c8d"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self._create_method_indicators(methods_frame)
        
        # === ROW 3: Score Display ===
        score_frame = ttk.Frame(container)
        score_frame.pack(fill=tk.X, pady=2)
        
        self._create_score_display(score_frame)
        
        # === ROW 4: Ranking Strategy ===
        strategy_frame = ttk.Frame(container)
        strategy_frame.pack(fill=tk.X, pady=2)
        
        self._create_strategy_display(strategy_frame)
    
    def _create_method_indicators(self, parent):
        """Erstellt Icons für Search Methods"""
        methods = self.source_data.get("search_methods", [])
        
        # Method Icons
        method_icons = {
            "vector": "🔍",
            "graph": "🕸️",
            "relational": "📊",
            "keyword": "🔤"
        }
        
        method_names = {
            "vector": "Vector Search",
            "graph": "Graph Search",
            "relational": "Relational Search",
            "keyword": "Keyword Search"
        }
        
        for method in methods:
            icon = method_icons.get(method, "❓")
            name = method_names.get(method, method)
            
            # Method Badge
            badge = ttk.Label(
                parent,
                text=f"{icon} {name}",
                font=("Segoe UI", 9),
                foreground="#3498db",
                background="#ecf0f1",
                padding=(5, 2)
            )
            badge.pack(side=tk.LEFT, padx=2)
            
            # Tooltip
            self._create_tooltip(badge, f"Ergebnis aus {name}")
    
    def _create_score_display(self, parent):
        """Erstellt Score-Anzeige mit Delta"""
        original = self.source_data.get("original_score", 0.0)
        reranked = self.source_data.get("reranked_score", 0.0)
        delta = self.source_data.get("score_delta", reranked - original)
        
        # Original Score
        ttk.Label(
            parent,
            text=f"Original Score: {original:.4f}",
            font=("Consolas", 9),
            foreground="#7f8c8d"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # Arrow
        ttk.Label(
            parent,
            text="→",
            font=("Segoe UI", 10),
            foreground="#95a5a6"
        ).pack(side=tk.LEFT, padx=5)
        
        # Reranked Score
        ttk.Label(
            parent,
            text=f"Reranked: {reranked:.4f}",
            font=("Consolas", 9, "bold"),
            foreground="#27ae60"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # Delta Badge
        self._create_delta_badge(parent, delta)
    
    def _create_delta_badge(self, parent, delta: float):
        """Erstellt farbiges Delta-Badge"""
        # Bestimme Farbe und Icon basierend auf Delta
        if delta > 0.01:
            icon = "📈"
            color = "#27ae60"  # Grün
            text = f"+{delta:.4f}"
        elif delta < -0.01:
            icon = "📉"
            color = "#e74c3c"  # Rot
            text = f"{delta:.4f}"
        else:
            icon = "➡️"
            color = "#95a5a6"  # Grau
            text = "±0.0000"
        
        # Badge Frame
        badge_frame = tk.Frame(
            parent,
            bg=color,
            relief=tk.RAISED,
            bd=1
        )
        badge_frame.pack(side=tk.LEFT, padx=5)
        
        # Icon + Text
        badge_label = tk.Label(
            badge_frame,
            text=f"{icon} {text}",
            font=("Consolas", 9, "bold"),
            bg=color,
            fg="white",
            padx=8,
            pady=2
        )
        badge_label.pack()
        
        # Tooltip
        tooltip_text = self._get_delta_tooltip(delta)
        self._create_tooltip(badge_frame, tooltip_text)
    
    def _get_delta_tooltip(self, delta: float) -> str:
        """Generiert Tooltip-Text für Score Delta"""
        if delta > 0.05:
            return "Stark verbessert durch Re-Ranking"
        elif delta > 0.01:
            return "Moderat verbessert durch Re-Ranking"
        elif delta < -0.05:
            return "Stark verschlechtert (unerwarteter Fall)"
        elif delta < -0.01:
            return "Leicht verschlechtert"
        else:
            return "Keine signifikante Änderung"
    
    def _create_strategy_display(self, parent):
        """Zeigt Ranking Strategy an"""
        strategy = self.source_data.get("ranking_strategy", "unknown")
        
        strategy_info = {
            "rrf": ("RRF (Reciprocal Rank Fusion)", "Kombiniert Rankings harmonisch"),
            "weighted": ("Weighted Combination", "Gewichtete Score-Aggregation"),
            "borda": ("Borda Count", "Positions-basiertes Ranking"),
            "unknown": ("Unbekannte Strategie", "Keine Strategie-Information")
        }
        
        display_name, description = strategy_info.get(strategy, strategy_info["unknown"])
        
        # Label
        strategy_label = ttk.Label(
            parent,
            text=f"Ranking: {display_name}",
            font=("Segoe UI", 9),
            foreground="#8e44ad"
        )
        strategy_label.pack(side=tk.LEFT)
        
        # Tooltip mit Beschreibung
        self._create_tooltip(strategy_label, description)
    
    def _create_tooltip(self, widget, text: str):
        """Erstellt Tooltip für Widget"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(
                tooltip,
                text=text,
                background="#2c3e50",
                foreground="white",
                relief=tk.SOLID,
                borderwidth=1,
                font=("Segoe UI", 9),
                padx=8,
                pady=5
            )
            label.pack()
            
            # Speichere Tooltip-Referenz
            widget._tooltip = tooltip
        
        def hide_tooltip(event):
            if hasattr(widget, '_tooltip'):
                widget._tooltip.destroy()
                del widget._tooltip
        
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)


class HybridSourcesPanel(ttk.Frame):
    """
    Panel zur Anzeige aller Hybrid Search Sources mit Metadata
    """
    
    def __init__(self, parent, sources: List[Dict[str, Any]], **kwargs):
        """
        Initialisiert das Sources Panel
        
        Args:
            parent: Parent Widget
            sources: Liste mit Source-Daten inkl. Hybrid Metadata
        """
        super().__init__(parent, **kwargs)
        self.sources = sources
        self._create_panel()
    
    def _create_panel(self):
        """Erstellt das vollständige Sources Panel"""
        # Title
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            title_frame,
            text=f"📚 Quellen ({len(self.sources)})",
            font=("Segoe UI", 12, "bold"),
            foreground="#2c3e50"
        ).pack(side=tk.LEFT)
        
        # Scrollable Container
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack Scrollbar & Canvas
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add Source Widgets
        for idx, source in enumerate(self.sources, start=1):
            self._create_source_card(scrollable_frame, idx, source)
    
    def _create_source_card(self, parent, index: int, source: Dict[str, Any]):
        """Erstellt eine Source Card mit Hybrid Metadata"""
        # Card Frame
        card = ttk.Frame(
            parent,
            relief=tk.RAISED,
            borderwidth=1,
            style="SourceCard.TFrame"
        )
        card.pack(fill=tk.X, padx=10, pady=5)
        
        # Header mit Index
        header = ttk.Frame(card)
        header.pack(fill=tk.X, padx=10, pady=(5, 0))
        
        ttk.Label(
            header,
            text=f"[{index}]",
            font=("Segoe UI", 10, "bold"),
            foreground="#3498db"
        ).pack(side=tk.LEFT)
        
        # Metadata Widget
        metadata_widget = HybridMetadataWidget(card, source)
        metadata_widget.pack(fill=tk.X, padx=10, pady=5)
        
        # Separator
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)


def create_hybrid_metadata_display(
    parent: tk.Widget,
    sources: List[Dict[str, Any]]
) -> HybridSourcesPanel:
    """
    Convenience-Funktion zum Erstellen eines Hybrid Sources Panels
    
    Args:
        parent: Parent Widget
        sources: Liste mit Hybrid Search Sources
        
    Returns:
        HybridSourcesPanel-Instanz
    
    Example:
        >>> sources = [
        ...     {
        ...         "title": "Dokument 1",
        ...         "original_score": 0.7500,
        ...         "reranked_score": 0.8500,
        ...         "score_delta": 0.1000,
        ...         "search_methods": ["vector", "graph"],
        ...         "ranking_strategy": "rrf"
        ...     }
        ... ]
        >>> panel = create_hybrid_metadata_display(root, sources)
        >>> panel.pack(fill=tk.BOTH, expand=True)
    """
    return HybridSourcesPanel(parent, sources)


# Styling Presets
def apply_hybrid_metadata_styles(root: tk.Tk):
    """
    Wendet vordefinierte Styles für Hybrid Metadata Widgets an
    
    Args:
        root: Root Tkinter Window
    """
    style = ttk.Style(root)
    
    # Hybrid Meta Frame
    style.configure(
        "HybridMeta.TFrame",
        background="#f8f9fa",
        relief=tk.FLAT
    )
    
    # Source Card Frame
    style.configure(
        "SourceCard.TFrame",
        background="white",
        relief=tk.RAISED,
        borderwidth=1
    )


if __name__ == "__main__":
    # === DEMO ===
    root = tk.Tk()
    root.title("Hybrid Metadata Widget Demo")
    root.geometry("800x600")
    
    apply_hybrid_metadata_styles(root)
    
    # Test Data
    test_sources = [
        {
            "title": "Klimawandel Bericht 2024",
            "original_score": 0.7234,
            "reranked_score": 0.8756,
            "score_delta": 0.1522,
            "search_methods": ["vector", "graph", "relational"],
            "ranking_strategy": "rrf"
        },
        {
            "title": "CO2 Emissionen Deutschland",
            "original_score": 0.6891,
            "reranked_score": 0.7123,
            "score_delta": 0.0232,
            "search_methods": ["vector"],
            "ranking_strategy": "weighted"
        },
        {
            "title": "Erneuerbare Energien Studie",
            "original_score": 0.8234,
            "reranked_score": 0.8195,
            "score_delta": -0.0039,
            "search_methods": ["vector", "keyword"],
            "ranking_strategy": "borda"
        }
    ]
    
    # Create Panel
    panel = create_hybrid_metadata_display(root, test_sources)
    panel.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    root.mainloop()
