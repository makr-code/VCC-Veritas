"""
Tests for PresentationCanvasAgent with Shapes, Diagrams, Arrows and Connectors

Tests:
1. Basic shapes (rectangles, circles, etc.)
2. Arrows (various types)
3. Flowchart diagrams
4. Organization charts
5. Cycle diagrams
6. Native PowerPoint shapes
7. Connectors
"""

import pytest
import asyncio
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.agents.presentation_canvas_agent import (
    PresentationCanvasAgent,
    VisualDescriptionLanguage
)


class TestBasicShapes:
    """Tests für Basis-Formen"""
    
    @pytest.mark.asyncio
    async def test_rectangle_shape(self):
        """Test: Rechteck erstellen"""
        agent = PresentationCanvasAgent()
        
        vdl = {
            "metadata": {"title": "Rectangle Test"},
            "use_native_shapes": True,
            "slides": [
                {
                    "layout": "blank",
                    "elements": [
                        {
                            "type": "shape",
                            "shape": "rectangle",
                            "content": "Test Rectangle",
                            "position": {"x": 100, "y": 100},
                            "size": {"width": 200, "height": 100},
                            "properties": {
                                "fill_color": "#4472c4",
                                "border_color": "#000000",
                                "border_width": 2
                            }
                        }
                    ]
                }
            ]
        }
        
        # Validierung
        is_valid, error = VisualDescriptionLanguage.validate(vdl)
        assert is_valid, f"VDL validation failed: {error}"
        
        # Rendering (nur PIL, kein PPTX in Test-Umgebung)
        slides = await agent._render_slides(vdl)
        assert len(slides) == 1
        assert slides[0]['slide_number'] == 1
    
    @pytest.mark.asyncio
    async def test_multiple_shapes(self):
        """Test: Mehrere verschiedene Formen"""
        agent = PresentationCanvasAgent()
        
        vdl = {
            "metadata": {"title": "Multiple Shapes Test"},
            "slides": [
                {
                    "layout": "blank",
                    "elements": [
                        {
                            "type": "shape",
                            "shape": "rectangle",
                            "position": {"x": 50, "y": 50},
                            "size": {"width": 100, "height": 80}
                        },
                        {
                            "type": "shape",
                            "shape": "oval",
                            "position": {"x": 200, "y": 50},
                            "size": {"width": 100, "height": 80}
                        },
                        {
                            "type": "shape",
                            "shape": "diamond",
                            "position": {"x": 350, "y": 50},
                            "size": {"width": 100, "height": 80}
                        }
                    ]
                }
            ]
        }
        
        is_valid, error = VisualDescriptionLanguage.validate(vdl)
        assert is_valid
        
        slides = await agent._render_slides(vdl)
        assert len(slides) == 1


class TestArrows:
    """Tests für Pfeil-Shapes"""
    
    @pytest.mark.asyncio
    async def test_basic_arrows(self):
        """Test: Basis-Pfeile (rechts, links, hoch, runter)"""
        agent = PresentationCanvasAgent()
        
        vdl = {
            "metadata": {"title": "Arrows Test"},
            "use_native_shapes": True,
            "slides": [
                {
                    "layout": "blank",
                    "elements": [
                        {
                            "type": "shape",
                            "shape": "right_arrow",
                            "position": {"x": 100, "y": 100},
                            "size": {"width": 150, "height": 60},
                            "properties": {"fill_color": "#ff9900"}
                        },
                        {
                            "type": "shape",
                            "shape": "left_arrow",
                            "position": {"x": 300, "y": 100},
                            "size": {"width": 150, "height": 60},
                            "properties": {"fill_color": "#0099ff"}
                        },
                        {
                            "type": "shape",
                            "shape": "circular_arrow",
                            "position": {"x": 500, "y": 100},
                            "size": {"width": 100, "height": 100},
                            "properties": {"fill_color": "#70ad47"}
                        }
                    ]
                }
            ]
        }
        
        is_valid, error = VisualDescriptionLanguage.validate(vdl)
        assert is_valid
        
        slides = await agent._render_slides(vdl)
        assert len(slides) == 1


class TestConnectors:
    """Tests für Verbindungslinien"""
    
    @pytest.mark.asyncio
    async def test_straight_connector(self):
        """Test: Gerade Verbindungslinie"""
        agent = PresentationCanvasAgent()
        
        vdl = {
            "metadata": {"title": "Connector Test"},
            "slides": [
                {
                    "layout": "blank",
                    "elements": [
                        {
                            "type": "shape",
                            "shape": "rectangle",
                            "content": "Start",
                            "position": {"x": 100, "y": 100},
                            "size": {"width": 100, "height": 80}
                        },
                        {
                            "type": "connector",
                            "connector_type": "straight",
                            "start": {"x": 200, "y": 140},
                            "end": {"x": 300, "y": 140},
                            "properties": {"width": 2, "color": "#000000"}
                        },
                        {
                            "type": "shape",
                            "shape": "rectangle",
                            "content": "Ende",
                            "position": {"x": 300, "y": 100},
                            "size": {"width": 100, "height": 80}
                        }
                    ]
                }
            ]
        }
        
        is_valid, error = VisualDescriptionLanguage.validate(vdl)
        assert is_valid
        
        slides = await agent._render_slides(vdl)
        assert len(slides) == 1


class TestFlowcharts:
    """Tests für Flussdiagramme"""
    
    @pytest.mark.asyncio
    async def test_simple_flowchart(self):
        """Test: Einfaches Flussdiagramm"""
        agent = PresentationCanvasAgent()
        
        vdl = {
            "metadata": {"title": "Flowchart Test"},
            "slides": [
                {
                    "layout": "blank",
                    "elements": [
                        {
                            "type": "flowchart",
                            "steps": [
                                {
                                    "shape": "flowchart_terminator",
                                    "text": "Start",
                                    "color": "#70ad47"
                                },
                                {
                                    "shape": "flowchart_process",
                                    "text": "Schritt 1",
                                    "color": "#4472c4"
                                },
                                {
                                    "shape": "flowchart_decision",
                                    "text": "Entscheidung?",
                                    "color": "#ed7d31"
                                },
                                {
                                    "shape": "flowchart_process",
                                    "text": "Schritt 2",
                                    "color": "#4472c4"
                                },
                                {
                                    "shape": "flowchart_terminator",
                                    "text": "Ende",
                                    "color": "#70ad47"
                                }
                            ],
                            "position": {"x": 300, "y": 50}
                        }
                    ]
                }
            ]
        }
        
        is_valid, error = VisualDescriptionLanguage.validate(vdl)
        assert is_valid
        
        slides = await agent._render_slides(vdl)
        assert len(slides) == 1
    
    @pytest.mark.asyncio
    async def test_bimschg_process_flowchart(self):
        """Test: BImSchG-Genehmigungsprozess als Flowchart"""
        agent = PresentationCanvasAgent()
        
        vdl = {
            "metadata": {"title": "BImSchG Genehmigungsprozess"},
            "use_native_shapes": True,
            "slides": [
                {
                    "layout": "content",
                    "elements": [
                        {
                            "type": "text",
                            "content": "BImSchG-Genehmigungsprozess",
                            "position": {"x": 50, "y": 30},
                            "size": {"width": 700, "height": 50},
                            "properties": {
                                "font_size": 32,
                                "font_weight": "bold"
                            }
                        },
                        {
                            "type": "flowchart",
                            "steps": [
                                {
                                    "shape": "flowchart_terminator",
                                    "text": "Antragstellung",
                                    "color": "#70ad47"
                                },
                                {
                                    "shape": "flowchart_process",
                                    "text": "Formale Prüfung",
                                    "color": "#4472c4"
                                },
                                {
                                    "shape": "flowchart_decision",
                                    "text": "Vollständig?",
                                    "color": "#ed7d31"
                                },
                                {
                                    "shape": "flowchart_process",
                                    "text": "Fachliche Prüfung",
                                    "color": "#4472c4"
                                },
                                {
                                    "shape": "flowchart_document",
                                    "text": "Auflagen definieren",
                                    "color": "#ffc000"
                                },
                                {
                                    "shape": "flowchart_terminator",
                                    "text": "Genehmigung erteilen",
                                    "color": "#70ad47"
                                }
                            ],
                            "position": {"x": 275, "y": 100}
                        }
                    ]
                }
            ]
        }
        
        is_valid, error = VisualDescriptionLanguage.validate(vdl)
        assert is_valid
        
        slides = await agent._render_slides(vdl)
        assert len(slides) == 1


class TestOrgCharts:
    """Tests für Organigramme"""
    
    @pytest.mark.asyncio
    async def test_simple_org_chart(self):
        """Test: Einfaches Organigramm"""
        agent = PresentationCanvasAgent()
        
        vdl = {
            "metadata": {"title": "Org Chart Test"},
            "slides": [
                {
                    "layout": "blank",
                    "elements": [
                        {
                            "type": "org_chart",
                            "levels": [
                                ["CEO"],
                                ["Manager 1", "Manager 2"],
                                ["Team A", "Team B", "Team C"]
                            ],
                            "position": {"x": 100, "y": 50}
                        }
                    ]
                }
            ]
        }
        
        is_valid, error = VisualDescriptionLanguage.validate(vdl)
        assert is_valid
        
        slides = await agent._render_slides(vdl)
        assert len(slides) == 1
    
    @pytest.mark.asyncio
    async def test_environmental_org_chart(self):
        """Test: Umweltbehörden-Organigramm"""
        agent = PresentationCanvasAgent()
        
        vdl = {
            "metadata": {"title": "Umweltbehörden Struktur"},
            "use_native_shapes": True,
            "slides": [
                {
                    "layout": "content",
                    "elements": [
                        {
                            "type": "text",
                            "content": "Organisationsstruktur Umweltabteilung",
                            "position": {"x": 50, "y": 30},
                            "size": {"width": 700, "height": 50},
                            "properties": {"font_size": 32}
                        },
                        {
                            "type": "org_chart",
                            "levels": [
                                ["Abteilungsleitung Umwelt"],
                                ["Immissionsschutz", "Naturschutz", "Gewässerschutz"],
                                ["BImSchG", "Lärm", "Flora", "Fauna", "Oberflächenwasser", "Grundwasser"]
                            ],
                            "position": {"x": 50, "y": 100}
                        }
                    ]
                }
            ]
        }
        
        is_valid, error = VisualDescriptionLanguage.validate(vdl)
        assert is_valid
        
        slides = await agent._render_slides(vdl)
        assert len(slides) == 1


class TestCycleDiagrams:
    """Tests für zyklische Diagramme"""
    
    @pytest.mark.asyncio
    async def test_pdca_cycle(self):
        """Test: PDCA-Zyklus (Plan-Do-Check-Act)"""
        agent = PresentationCanvasAgent()
        
        vdl = {
            "metadata": {"title": "PDCA Cycle"},
            "slides": [
                {
                    "layout": "blank",
                    "elements": [
                        {
                            "type": "cycle_diagram",
                            "steps": ["Plan", "Do", "Check", "Act"],
                            "position": {"x": 400, "y": 300}
                        }
                    ]
                }
            ]
        }
        
        is_valid, error = VisualDescriptionLanguage.validate(vdl)
        assert is_valid
        
        slides = await agent._render_slides(vdl)
        assert len(slides) == 1


class TestNativeShapes:
    """Tests für native PowerPoint-Shapes"""
    
    @pytest.mark.asyncio
    async def test_native_shapes_flag(self):
        """Test: use_native_shapes Flag"""
        agent = PresentationCanvasAgent()
        
        vdl = {
            "metadata": {"title": "Native Shapes Test"},
            "use_native_shapes": True,  # ← Wichtig!
            "slides": [
                {
                    "layout": "blank",
                    "elements": [
                        {
                            "type": "shape",
                            "shape": "flowchart_process",
                            "content": "Editierbar in PowerPoint!",
                            "position": {"x": 200, "y": 200},
                            "size": {"width": 400, "height": 100},
                            "properties": {
                                "fill_color": "#4472c4",
                                "border_color": "#000000",
                                "border_width": 2
                            }
                        }
                    ]
                }
            ]
        }
        
        is_valid, error = VisualDescriptionLanguage.validate(vdl)
        assert is_valid


class TestComplexPresentations:
    """Tests für komplexe Multi-Slide-Präsentationen"""
    
    @pytest.mark.asyncio
    async def test_bimschg_presentation(self):
        """Test: Vollständige BImSchG-Präsentation"""
        agent = PresentationCanvasAgent()
        
        vdl = {
            "metadata": {
                "title": "BImSchG-Anlagen in Brandenburg",
                "author": "VERITAS Canvas Agent",
                "theme": "professional"
            },
            "use_native_shapes": True,
            "slides": [
                # Slide 1: Titel
                {
                    "layout": "title_slide",
                    "elements": [
                        {
                            "type": "text",
                            "content": "BImSchG-Anlagen in Brandenburg",
                            "position": {"x": 50, "y": 200},
                            "size": {"width": 700, "height": 100},
                            "properties": {
                                "font_size": 44,
                                "font_weight": "bold",
                                "align": "center",
                                "color": "#1f4788"
                            }
                        },
                        {
                            "type": "text",
                            "content": "Genehmigungsprozess und Organisation",
                            "position": {"x": 50, "y": 320},
                            "size": {"width": 700, "height": 50},
                            "properties": {
                                "font_size": 24,
                                "align": "center",
                                "color": "#666666"
                            }
                        }
                    ]
                },
                # Slide 2: Prozess
                {
                    "layout": "content",
                    "elements": [
                        {
                            "type": "text",
                            "content": "Genehmigungsprozess",
                            "position": {"x": 50, "y": 30},
                            "size": {"width": 700, "height": 50},
                            "properties": {"font_size": 32}
                        },
                        {
                            "type": "flowchart",
                            "steps": [
                                {"shape": "flowchart_terminator", "text": "Antragstellung", "color": "#70ad47"},
                                {"shape": "flowchart_process", "text": "Formale Prüfung", "color": "#4472c4"},
                                {"shape": "flowchart_decision", "text": "Vollständig?", "color": "#ed7d31"},
                                {"shape": "flowchart_process", "text": "Fachliche Prüfung", "color": "#4472c4"},
                                {"shape": "flowchart_terminator", "text": "Genehmigung", "color": "#70ad47"}
                            ],
                            "position": {"x": 275, "y": 100}
                        }
                    ]
                },
                # Slide 3: Organisation
                {
                    "layout": "content",
                    "elements": [
                        {
                            "type": "text",
                            "content": "Organisationsstruktur",
                            "position": {"x": 50, "y": 30},
                            "size": {"width": 700, "height": 50},
                            "properties": {"font_size": 32}
                        },
                        {
                            "type": "org_chart",
                            "levels": [
                                ["Umweltbehörde"],
                                ["Immissionsschutz", "Naturschutz"],
                                ["BImSchG", "Lärm", "Flora", "Fauna"]
                            ],
                            "position": {"x": 100, "y": 100}
                        }
                    ]
                }
            ]
        }
        
        is_valid, error = VisualDescriptionLanguage.validate(vdl)
        assert is_valid, f"VDL validation failed: {error}"
        
        slides = await agent._render_slides(vdl)
        assert len(slides) == 3


# Standalone-Ausführung für manuelle Tests
if __name__ == '__main__':
    print("=== PresentationCanvasAgent - Shapes & Diagrams Tests ===\n")
    
    async def run_all_tests():
        """Führt alle Tests aus (manuell)"""
        
        # Test 1: Basis-Shapes
        print("Test 1: Basis-Shapes...")
        test = TestBasicShapes()
        await test.test_rectangle_shape()
        print("✅ Basis-Shapes Test erfolgreich\n")
        
        # Test 2: Pfeile
        print("Test 2: Pfeile...")
        test = TestArrows()
        await test.test_basic_arrows()
        print("✅ Pfeile Test erfolgreich\n")
        
        # Test 3: Connectors
        print("Test 3: Connectors...")
        test = TestConnectors()
        await test.test_straight_connector()
        print("✅ Connectors Test erfolgreich\n")
        
        # Test 4: Flowcharts
        print("Test 4: Flowcharts...")
        test = TestFlowcharts()
        await test.test_simple_flowchart()
        await test.test_bimschg_process_flowchart()
        print("✅ Flowcharts Test erfolgreich\n")
        
        # Test 5: Organigramme
        print("Test 5: Organigramme...")
        test = TestOrgCharts()
        await test.test_simple_org_chart()
        await test.test_environmental_org_chart()
        print("✅ Organigramme Test erfolgreich\n")
        
        # Test 6: Zyklische Diagramme
        print("Test 6: Zyklische Diagramme...")
        test = TestCycleDiagrams()
        await test.test_pdca_cycle()
        print("✅ Zyklische Diagramme Test erfolgreich\n")
        
        # Test 7: Komplexe Präsentation
        print("Test 7: Komplexe Präsentation...")
        test = TestComplexPresentations()
        await test.test_bimschg_presentation()
        print("✅ Komplexe Präsentation Test erfolgreich\n")
        
        print("=" * 60)
        print("✅ ALLE TESTS ERFOLGREICH!")
        print("=" * 60)
    
    asyncio.run(run_all_tests())
