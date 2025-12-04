"""
VERITAS Visualization Agent Dispatcher
======================================

Dispatcher für Visualisierungs- und Generierungs-Agents
Wird vom Orchestrator/Pipeline Manager genutzt

Author: VERITAS System
Date: 2025-12-04
Version: 1.0
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# =========================================================================
# Visualization Agent Dispatcher
# =========================================================================


async def dispatch_chart_generation(context: Dict[str, Any], chart_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Dispatch Chart Generation Agent

    Args:
        context: Query context mit chart_data, chart_type, etc.
        chart_data: Optional explicit chart data

    Returns:
        Dict with chart_id, export_html, status
    """
    try:
        import uuid

        from backend.visualization.chart_engine import ChartConfig, ChartType, DataSeries, get_chart_manager

        manager = get_chart_manager()

        # Extract chart data from context
        if chart_data is None:
            chart_data = context.get("chart_data", {})

        chart_type_str = chart_data.get("type", "line").upper()

        # Map string to ChartType enum
        try:
            chart_type = ChartType[chart_type_str]
        except KeyError:
            chart_type = ChartType.LINE

        # Create chart config
        config = ChartConfig(title=chart_data.get("title", "Chart"), chart_type=chart_type)

        # Create chart with ID and config
        chart_id = str(uuid.uuid4())[:8]
        chart = manager.create_chart(chart_id=chart_id, config=config)

        # Add data series - convert dicts to DataSeries objects
        for series_data in chart_data.get("series", []):
            if isinstance(series_data, dict):
                series = DataSeries(
                    name=series_data.get("name", "Series"),
                    x_values=series_data.get("x_values", series_data.get("x", [])),
                    y_values=series_data.get("y_values", series_data.get("y", [])),
                    color=series_data.get("color"),
                    line_style=series_data.get("line_style", "solid"),
                    marker_type=series_data.get("marker_type"),
                )
            else:
                series = series_data  # Already a DataSeries object

            chart.add_series(series)

        # Generate chart data (render internally)
        chart_output = await chart.generate_chart()

        # Build HTML/JSON exports manually to avoid asyncio.run() issue
        # Instead of calling chart.export_html() which uses asyncio.run()
        html_export = f"<html><body><h1>{config.title}</h1><pre>{json.dumps(chart_output, indent=2)}</pre></body></html>"
        json_export = json.dumps(chart_output, indent=2, default=str)

        return {
            "status": "success",
            "agent_type": "chart_engine",
            "chart_id": chart_id,
            "chart_type": chart_type.value,
            "chart_data": chart_output,
            "export_html": html_export,
            "export_json": json_export,
        }

    except Exception as e:
        logger.error(f"Chart generation failed: {e}")
        return {"status": "error", "agent_type": "chart_engine", "error": str(e)}


async def dispatch_presentation_creation(
    context: Dict[str, Any], prompt: Optional[str] = None, num_slides: int = 3
) -> Dict[str, Any]:
    """
    Dispatch Presentation Canvas Agent

    Args:
        context: Query context mit presentation_prompt, num_slides, etc.
        prompt: Optional explicit prompt
        num_slides: Number of slides to generate

    Returns:
        Dict with vdl, pptx_path, status
    """
    try:
        from backend.agents.presentation_canvas_agent import PresentationCanvasAgent

        agent = PresentationCanvasAgent()

        # Get prompt
        if prompt is None:
            prompt = context.get("presentation_prompt", "Create a professional presentation")

        # Generate presentation
        result = await agent.generate_presentation(user_prompt=prompt, context=context)

        # Extract results
        if not result.get("success", False):
            return {"status": "error", "agent_type": "presentation_canvas", "error": "Presentation generation failed"}

        return {
            "status": "success",
            "agent_type": "presentation_canvas",
            "slide_count": len(result.get("slides", [])),
            "pptx_path": result.get("pptx_path"),
            "vdl": result.get("vdl"),
        }

    except Exception as e:
        logger.error(f"Presentation creation failed: {e}")
        return {"status": "error", "agent_type": "presentation_canvas", "error": str(e)}


async def dispatch_image_generation(context: Dict[str, Any], prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """
    Dispatch Image Generation Agent

    Args:
        context: Query context mit image_prompt, model, width, height, etc.
        prompt: Optional explicit prompt
        **kwargs: Additional generation parameters

    Returns:
        Dict with image_id, status, processing_time
    """
    try:
        from backend.imaging.integration import get_image_generation_agent

        agent = get_image_generation_agent()

        # Build request data
        request_data = {
            "prompt": prompt or context.get("image_prompt", ""),
            "model": context.get("model", "sdxl"),
            "width": context.get("width", 768),
            "height": context.get("height", 768),
            "quality": context.get("quality", "high"),
            "steps": context.get("steps", 20),
            "guidance": context.get("guidance", 7.5),
            **kwargs,
        }

        # Generate image
        result = await agent.process_request(request_data)

        return {
            "status": result.get("status", "error"),
            "agent_type": "image_generation",
            "image_id": result.get("image_id"),
            "model": result.get("model"),
            "processing_time_ms": result.get("processing_time_ms"),
            "error": result.get("error"),
        }

    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return {"status": "error", "agent_type": "image_generation", "error": str(e)}


async def dispatch_map_generation(
    context: Dict[str, Any], geo_data: Optional[list[Dict[str, Any]]] = None, map_spec: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Dispatch Geo Map Agent (OSM)

    Args:
        context: Query context with geo_query, map_spec
        geo_data: Optional explicit geodata
        map_spec: Optional map specification

    Returns:
        Dict with image_base64, png_path, feature_count, status
    """
    try:
        from backend.agents.geo_sub_agent import GeoSubAgent

        agent = GeoSubAgent()

        # Get geo data if not provided
        if geo_data is None:
            geo_query = context.get("geo_query", {})
            if geo_query:
                geo_data = await agent.get_geo_data(geo_query)
            else:
                # Use example data for testing
                geo_data = agent._get_example_geo_data()

        # Build map specification
        if map_spec is None:
            map_spec = context.get("map_spec", {})

        # Set defaults
        map_spec.setdefault("center", [52.5, 13.0])  # Brandenburg center
        map_spec.setdefault("zoom", 8)
        map_spec.setdefault("width", 800)
        map_spec.setdefault("height", 600)
        map_spec.setdefault("title", "OSM Map")
        map_spec.setdefault("style", "markers")

        # Generate map
        result = await agent.generate_map(geo_data, map_spec)

        if result.get("success"):
            return {
                "status": "success",
                "agent_type": "geo_map",
                "image_base64": result.get("image_base64"),
                "png_path": result.get("png_path"),
                "geojson": result.get("geojson"),
                "feature_count": result.get("feature_count"),
            }
        else:
            return {"status": "error", "agent_type": "geo_map", "error": result.get("error", "Map generation failed")}

    except Exception as e:
        logger.error(f"Map generation failed: {e}")
        return {"status": "error", "agent_type": "geo_map", "error": str(e)}


# =========================================================================
# Unified Dispatcher (capability-based)
# =========================================================================


async def dispatch_visualization_agent(capability: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Unified dispatcher for visualization agents

    Args:
        capability: Agent capability (chart_generation, presentation_creation, image_generation, map_generation)
        context: Query context

    Returns:
        Dict with agent result
    """
    if capability == "chart_generation":
        return await dispatch_chart_generation(context)

    elif capability == "presentation_creation":
        return await dispatch_presentation_creation(context)

    elif capability == "image_generation":
        return await dispatch_image_generation(context)

    elif capability == "map_generation":
        return await dispatch_map_generation(context)

    else:
        return {"status": "error", "error": f"Unknown visualization capability: {capability}"}


# =========================================================================
# Batch Processing
# =========================================================================


async def dispatch_visualization_batch(tasks: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """
    Dispatch multiple visualization tasks in parallel

    Args:
        tasks: List of task dicts with 'capability' and 'context'

    Returns:
        List of results
    """
    coroutines = [dispatch_visualization_agent(task["capability"], task["context"]) for task in tasks]

    results = await asyncio.gather(*coroutines, return_exceptions=True)

    # Convert exceptions to error dicts
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed_results.append({"status": "error", "error": str(result), "task_index": i})
        else:
            processed_results.append(result)

    return processed_results
