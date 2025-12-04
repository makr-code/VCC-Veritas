"""
VERITAS Chart Integration Engine - Visualization Module

Unified chart generation system with support for:
- Line charts (time series)
- Bar charts (categories)
- Pie charts (distributions)
- Heatmaps (correlations)
- Scatter plots (relationships)
- Combined visualizations

Framework:
- Plotly for interactive visualizations
- Matplotlib for static export
- Real-time data streaming
- Export to JSON/HTML/PNG

Author: VERITAS Visualization Engine
Date: 2025-12-04
Version: 1.0
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# =========================================================================
# Chart Types & Configuration
# =========================================================================


class ChartType(Enum):
    """Supported chart types"""

    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    HISTOGRAM = "histogram"
    BOX = "box"
    WATERFALL = "waterfall"


class ColorScheme(Enum):
    """Color schemes for charts"""

    VIRIDIS = "viridis"
    PLASMA = "plasma"
    COOL = "cool"
    VERITAS = "veritas"  # Custom VERITAS theme
    DARK = "dark"


@dataclass
class ChartConfig:
    """Chart configuration"""

    title: str
    chart_type: ChartType
    x_axis_label: Optional[str] = None
    y_axis_label: Optional[str] = None
    color_scheme: ColorScheme = ColorScheme.VERITAS
    width: int = 1200
    height: int = 600
    show_legend: bool = True
    show_grid: bool = True
    interactive: bool = True
    export_format: str = "html"  # html, json, png, svg


@dataclass
class DataSeries:
    """Single data series"""

    name: str
    x_values: List[Any]
    y_values: List[float]
    color: Optional[str] = None
    line_style: str = "solid"  # solid, dashed, dotted
    marker_type: Optional[str] = None  # circle, square, diamond
    metadata: Dict[str, Any] = None


# =========================================================================
# Chart Engine Core
# =========================================================================


class ChartEngine:
    """
    VERITAS Chart Generation Engine

    Provides unified interface for chart creation and manipulation.
    Supports real-time updates and interactive visualizations.
    """

    def __init__(self, config: ChartConfig):
        """Initialize chart engine"""
        self.config = config
        self.series: List[DataSeries] = []
        self.chart_data: Dict[str, Any] = {}
        self.created_at = datetime.now()

        logger.info(f"📊 ChartEngine initialized: {config.title}")

    def add_series(self, series: DataSeries) -> None:
        """Add data series to chart"""
        if len(series.x_values) != len(series.y_values):
            raise ValueError(f"Series {series.name}: x and y lengths don't match")

        self.series.append(series)
        logger.debug(f"Added series: {series.name} ({len(series.x_values)} points)")

    def add_data(self, name: str, x_values: List[Any], y_values: List[float]) -> None:
        """Quick method to add data series"""
        series = DataSeries(name=name, x_values=x_values, y_values=y_values)
        self.add_series(series)

    async def generate_chart(self) -> Dict[str, Any]:
        """Generate chart data structure"""
        return await self._render_chart()

    async def _render_chart(self) -> Dict[str, Any]:
        """Render chart based on type"""
        if self.config.chart_type == ChartType.LINE:
            return self._render_line_chart()
        elif self.config.chart_type == ChartType.BAR:
            return self._render_bar_chart()
        elif self.config.chart_type == ChartType.PIE:
            return self._render_pie_chart()
        elif self.config.chart_type == ChartType.SCATTER:
            return self._render_scatter_chart()
        elif self.config.chart_type == ChartType.HEATMAP:
            return self._render_heatmap()
        else:
            raise ValueError(f"Unsupported chart type: {self.config.chart_type}")

    def _render_line_chart(self) -> Dict[str, Any]:
        """Render line chart"""
        traces = []
        for i, series in enumerate(self.series):
            trace = {
                "type": "scatter",
                "mode": "lines+markers" if series.marker_type else "lines",
                "name": series.name,
                "x": series.x_values,
                "y": series.y_values,
                "line": {
                    "color": series.color or self._get_color(i),
                    "dash": "solid" if series.line_style == "solid" else series.line_style,
                },
            }
            if series.marker_type:
                trace["marker"] = {"symbol": series.marker_type}
            traces.append(trace)

        return {"data": traces, "layout": self._get_layout(), "type": "line"}

    def _render_bar_chart(self) -> Dict[str, Any]:
        """Render bar chart"""
        traces = []
        for i, series in enumerate(self.series):
            trace = {
                "type": "bar",
                "name": series.name,
                "x": series.x_values,
                "y": series.y_values,
                "marker": {"color": series.color or self._get_color(i)},
            }
            traces.append(trace)

        return {"data": traces, "layout": self._get_layout(), "type": "bar"}

    def _render_pie_chart(self) -> Dict[str, Any]:
        """Render pie chart"""
        if len(self.series) != 1:
            raise ValueError("Pie chart requires exactly one data series")

        series = self.series[0]
        trace = {
            "type": "pie",
            "labels": series.x_values,
            "values": series.y_values,
            "marker": {"colors": [self._get_color(i) for i in range(len(series.y_values))]},
        }

        return {"data": [trace], "layout": self._get_layout(), "type": "pie"}

    def _render_scatter_chart(self) -> Dict[str, Any]:
        """Render scatter plot"""
        traces = []
        for i, series in enumerate(self.series):
            trace = {
                "type": "scatter",
                "mode": "markers",
                "name": series.name,
                "x": series.x_values,
                "y": series.y_values,
                "marker": {"color": series.color or self._get_color(i), "size": 8, "symbol": series.marker_type or "circle"},
            }
            traces.append(trace)

        return {"data": traces, "layout": self._get_layout(), "type": "scatter"}

    def _render_heatmap(self) -> Dict[str, Any]:
        """Render heatmap"""
        if len(self.series) == 0:
            raise ValueError("Heatmap requires data")

        # For heatmap, x_values should be columns, y_values should be rows
        series = self.series[0]
        trace = {"type": "heatmap", "z": series.y_values, "x": series.x_values, "colorscale": "Viridis"}

        return {"data": [trace], "layout": self._get_layout(), "type": "heatmap"}

    def _get_layout(self) -> Dict[str, Any]:
        """Get chart layout configuration"""
        return {
            "title": {"text": self.config.title, "font": {"size": 24}},
            "xaxis": {"title": self.config.x_axis_label or "X Axis", "showgrid": self.config.show_grid},
            "yaxis": {"title": self.config.y_axis_label or "Y Axis", "showgrid": self.config.show_grid},
            "width": self.config.width,
            "height": self.config.height,
            "showlegend": self.config.show_legend,
            "hovermode": "closest" if self.config.interactive else False,
            "template": "plotly_dark" if self.config.color_scheme == ColorScheme.DARK else "plotly",
        }

    def _get_color(self, index: int) -> str:
        """Get color from scheme"""
        colors = {
            ColorScheme.VIRIDIS: ["#440154", "#31688e", "#35b779", "#fde724"],
            ColorScheme.PLASMA: ["#0d0887", "#46039f", "#7201a8", "#b73779"],
            ColorScheme.COOL: ["#003f5c", "#58508d", "#bc5090", "#ff6361"],
            ColorScheme.VERITAS: ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"],
            ColorScheme.DARK: ["#e74c3c", "#3498db", "#2ecc71", "#f39c12"],
        }

        color_list = colors.get(self.config.color_scheme, colors[ColorScheme.VERITAS])
        return color_list[index % len(color_list)]

    def export_json(self) -> str:
        """Export chart as JSON"""
        chart_data = asyncio.run(self.generate_chart())
        return json.dumps(chart_data, indent=2, default=str)

    def export_html(self) -> str:
        """Export chart as interactive HTML"""
        chart_data = asyncio.run(self.generate_chart())

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{self.config.title}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        #chart {{ width: 100%; height: 100vh; }}
        .info {{ color: #666; font-size: 12px; margin-top: 10px; }}
    </style>
</head>
<body>
    <h1>{self.config.title}</h1>
    <div id="chart"></div>
    <div class="info">
        <p>Chart Type: {self.config.chart_type.value}</p>
        <p>Generated: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    <script>
        const data = {json.dumps(chart_data['data'])};
        const layout = {json.dumps(chart_data['layout'])};
        Plotly.newPlot('chart', data, layout, {{responsive: true}});
    </script>
</body>
</html>"""
        return html

    def get_info(self) -> Dict[str, Any]:
        """Get chart information"""
        return {
            "title": self.config.title,
            "type": self.config.chart_type.value,
            "series_count": len(self.series),
            "series_names": [s.name for s in self.series],
            "width": self.config.width,
            "height": self.config.height,
            "interactive": self.config.interactive,
            "created_at": self.created_at.isoformat(),
        }


# =========================================================================
# Chart Manager - High-Level API
# =========================================================================


class ChartManager:
    """
    High-level chart management system.

    Provides simple interface for creating and managing multiple charts.
    Integrates with VERITAS data pipeline.
    """

    def __init__(self):
        """Initialize chart manager"""
        self.charts: Dict[str, ChartEngine] = {}
        logger.info("📊 ChartManager initialized")

    def create_chart(self, chart_id: str, config: ChartConfig) -> ChartEngine:
        """Create new chart"""
        if chart_id in self.charts:
            logger.warning(f"Chart '{chart_id}' already exists, overwriting")

        chart = ChartEngine(config)
        self.charts[chart_id] = chart
        return chart

    def get_chart(self, chart_id: str) -> Optional[ChartEngine]:
        """Get chart by ID"""
        return self.charts.get(chart_id)

    def delete_chart(self, chart_id: str) -> bool:
        """Delete chart"""
        if chart_id in self.charts:
            del self.charts[chart_id]
            logger.info(f"Chart '{chart_id}' deleted")
            return True
        return False

    def list_charts(self) -> List[Dict[str, Any]]:
        """List all charts"""
        return [chart.get_info() for chart in self.charts.values()]

    def export_chart(self, chart_id: str, format: str = "html") -> Optional[str]:
        """Export chart in specific format"""
        chart = self.get_chart(chart_id)
        if not chart:
            return None

        if format == "json":
            return chart.export_json()
        elif format == "html":
            return chart.export_html()
        else:
            raise ValueError(f"Unsupported export format: {format}")


# =========================================================================
# Singleton Instance
# =========================================================================

_chart_manager = None


def get_chart_manager() -> ChartManager:
    """Get or create chart manager singleton"""
    global _chart_manager
    if _chart_manager is None:
        _chart_manager = ChartManager()
    return _chart_manager
