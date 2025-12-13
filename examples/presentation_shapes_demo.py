"""
Demonstration: PowerPoint-Präsentationen mit Diagrammen, Formen, Pfeilen und Connectors

Dieses Beispiel zeigt, wie man den erweiterten PresentationCanvasAgent nutzt, um
professionelle Präsentationen mit nativen PowerPoint-Shapes zu erstellen.

Neue Funktionen (Dezember 2025):
- ✅ 182+ verschiedene Formen (Shapes)
- ✅ 29 Pfeil-Typen
- ✅ 29 Flussdiagramm-Formen
- ✅ Connectors (Verbindungslinien)
- ✅ Diagram-Templates (Organigramm, Prozessflow, Zyklus)
- ✅ Native PowerPoint-Shapes (editierbar in PowerPoint)
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.agents.presentation_canvas_agent import PresentationCanvasAgent


async def demo_1_basic_shapes():
    """Demo 1: Basis-Formen und Pfeile"""
    print("\n" + "="*60)
    print("DEMO 1: Basis-Formen und Pfeile")
    print("="*60)
    
    agent = PresentationCanvasAgent()
    
    vdl = {
        "metadata": {
            "title": "Basis-Formen Demo",
            "author": "VERITAS",
            "theme": "professional"
        },
        "use_native_shapes": True,  # Native PowerPoint-Shapes!
        "slides": [
            {
                "layout": "content",
                "elements": [
                    {
                        "type": "text",
                        "content": "Verschiedene Formen und Pfeile",
                        "position": {"x": 50, "y": 30},
                        "size": {"width": 700, "height": 50},
                        "properties": {
                            "font_size": 32,
                            "font_weight": "bold"
                        }
                    },
                    # Rechteck
                    {
                        "type": "shape",
                        "shape": "rectangle",
                        "content": "Rechteck",
                        "position": {"x": 50, "y": 100},
                        "size": {"width": 150, "height": 100},
                        "properties": {
                            "fill_color": "#4472c4",
                            "border_color": "#000000",
                            "border_width": 2
                        }
                    },
                    # Kreis
                    {
                        "type": "shape",
                        "shape": "oval",
                        "content": "Kreis",
                        "position": {"x": 250, "y": 100},
                        "size": {"width": 150, "height": 100},
                        "properties": {
                            "fill_color": "#70ad47",
                            "border_color": "#000000",
                            "border_width": 2
                        }
                    },
                    # Diamant
                    {
                        "type": "shape",
                        "shape": "diamond",
                        "content": "Diamant",
                        "position": {"x": 450, "y": 100},
                        "size": {"width": 150, "height": 100},
                        "properties": {
                            "fill_color": "#ed7d31",
                            "border_color": "#000000",
                            "border_width": 2
                        }
                    },
                    # Pfeil rechts
                    {
                        "type": "shape",
                        "shape": "right_arrow",
                        "content": "→",
                        "position": {"x": 50, "y": 250},
                        "size": {"width": 200, "height": 80},
                        "properties": {
                            "fill_color": "#ffc000",
                            "border_color": "#000000",
                            "border_width": 2
                        }
                    },
                    # Kreisförmiger Pfeil
                    {
                        "type": "shape",
                        "shape": "circular_arrow",
                        "position": {"x": 300, "y": 250},
                        "size": {"width": 100, "height": 100},
                        "properties": {
                            "fill_color": "#5b9bd5",
                            "border_color": "#000000",
                            "border_width": 2
                        }
                    },
                    # Bidirektionaler Pfeil
                    {
                        "type": "shape",
                        "shape": "left_right_arrow",
                        "content": "↔",
                        "position": {"x": 450, "y": 250},
                        "size": {"width": 200, "height": 80},
                        "properties": {
                            "fill_color": "#a5a5a5",
                            "border_color": "#000000",
                            "border_width": 2
                        }
                    }
                ]
            }
        ]
    }
    
    result = await agent.generate_presentation(
        user_prompt="Erstelle eine Präsentation mit verschiedenen Formen",
        context={"vdl_override": vdl}  # Für Demo nutzen wir direktes VDL
    )
    
    if result.get('success'):
        print(f"✅ Präsentation erstellt!")
        print(f"   Folien: {result['slide_count']}")
        if result.get('pptx_path'):
            print(f"   PPTX: {result['pptx_path']}")
            print(f"   → Öffne in PowerPoint und bearbeite die Shapes!")
    else:
        print(f"❌ Fehler: {result.get('error')}")


async def demo_2_flowchart():
    """Demo 2: Flussdiagramm (BImSchG-Genehmigungsprozess)"""
    print("\n" + "="*60)
    print("DEMO 2: Flussdiagramm - BImSchG-Genehmigungsprozess")
    print("="*60)
    
    agent = PresentationCanvasAgent()
    
    vdl = {
        "metadata": {
            "title": "BImSchG-Genehmigungsprozess",
            "author": "VERITAS Umwelt-Agent",
            "theme": "professional"
        },
        "use_native_shapes": True,
        "slides": [
            {
                "layout": "title_slide",
                "elements": [
                    {
                        "type": "text",
                        "content": "BImSchG-Genehmigungsprozess",
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
                        "content": "Bundesimmissionsschutzgesetz - Verfahrensablauf",
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
            {
                "layout": "content",
                "elements": [
                    {
                        "type": "text",
                        "content": "Verfahrensablauf im Detail",
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
                                "text": "Formale Vollständigkeitsprüfung",
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
                                "shape": "flowchart_decision",
                                "text": "Genehmigungsfähig?",
                                "color": "#ed7d31"
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
    
    # Simuliere Präsentations-Generierung
    slides = await agent._render_slides(vdl)
    pptx_path = agent._create_pptx(vdl, slides)
    
    print(f"✅ Flowchart-Präsentation erstellt!")
    print(f"   Folien: {len(slides)}")
    print(f"   PPTX: {pptx_path}")
    print(f"   → Flussdiagramm mit 7 Schritten")
    print(f"   → Editierbar in PowerPoint (native Shapes!)")


async def demo_3_org_chart():
    """Demo 3: Organigramm (Umweltbehörde)"""
    print("\n" + "="*60)
    print("DEMO 3: Organigramm - Umweltbehörden-Struktur")
    print("="*60)
    
    agent = PresentationCanvasAgent()
    
    vdl = {
        "metadata": {
            "title": "Organisationsstruktur Umweltbehörde",
            "author": "VERITAS",
            "theme": "professional"
        },
        "use_native_shapes": True,
        "slides": [
            {
                "layout": "content",
                "elements": [
                    {
                        "type": "text",
                        "content": "Organisationsstruktur",
                        "position": {"x": 50, "y": 30},
                        "size": {"width": 700, "height": 50},
                        "properties": {
                            "font_size": 32,
                            "font_weight": "bold"
                        }
                    },
                    {
                        "type": "org_chart",
                        "levels": [
                            ["Leitung Umweltbehörde"],
                            ["Immissionsschutz", "Naturschutz", "Gewässerschutz"],
                            ["BImSchG", "Lärm", "Luftreinhaltung", "Flora", "Fauna", "Biotope", "Oberflächenwasser", "Grundwasser"]
                        ],
                        "position": {"x": 50, "y": 100}
                    }
                ]
            }
        ]
    }
    
    slides = await agent._render_slides(vdl)
    pptx_path = agent._create_pptx(vdl, slides)
    
    print(f"✅ Organigramm erstellt!")
    print(f"   Folien: {len(slides)}")
    print(f"   PPTX: {pptx_path}")
    print(f"   → 3 Ebenen: Leitung → Abteilungen → Teams")
    print(f"   → Mit Connectors verbunden")


async def demo_4_cycle_diagram():
    """Demo 4: Zyklisches Diagramm (PDCA)"""
    print("\n" + "="*60)
    print("DEMO 4: Zyklisches Diagramm - PDCA-Zyklus")
    print("="*60)
    
    agent = PresentationCanvasAgent()
    
    vdl = {
        "metadata": {
            "title": "Kontinuierlicher Verbesserungsprozess",
            "author": "VERITAS",
            "theme": "professional"
        },
        "use_native_shapes": True,
        "slides": [
            {
                "layout": "content",
                "elements": [
                    {
                        "type": "text",
                        "content": "PDCA-Zyklus (Plan-Do-Check-Act)",
                        "position": {"x": 50, "y": 30},
                        "size": {"width": 700, "height": 50},
                        "properties": {
                            "font_size": 32,
                            "font_weight": "bold",
                            "align": "center"
                        }
                    },
                    {
                        "type": "cycle_diagram",
                        "steps": [
                            "Plan\n(Planen)",
                            "Do\n(Umsetzen)",
                            "Check\n(Überprüfen)",
                            "Act\n(Handeln)"
                        ],
                        "position": {"x": 400, "y": 300}
                    }
                ]
            }
        ]
    }
    
    slides = await agent._render_slides(vdl)
    pptx_path = agent._create_pptx(vdl, slides)
    
    print(f"✅ Zyklisches Diagramm erstellt!")
    print(f"   Folien: {len(slides)}")
    print(f"   PPTX: {pptx_path}")
    print(f"   → 4 Schritte im Kreis angeordnet")
    print(f"   → Kontinuierlicher Verbesserungsprozess")


async def demo_5_complete_presentation():
    """Demo 5: Komplette Präsentation mit allen Features"""
    print("\n" + "="*60)
    print("DEMO 5: Komplette Präsentation - Alle Features")
    print("="*60)
    
    agent = PresentationCanvasAgent()
    
    vdl = {
        "metadata": {
            "title": "BImSchG-Anlagen - Komplett",
            "author": "VERITAS Environmental Agent",
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
                        "content": "Genehmigung, Organisation und Prozesse",
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
            # Slide 2: Genehmigungsprozess (Flowchart)
            {
                "layout": "content",
                "elements": [
                    {
                        "type": "text",
                        "content": "Genehmigungsprozess",
                        "position": {"x": 50, "y": 30},
                        "size": {"width": 700, "height": 50},
                        "properties": {"font_size": 32, "font_weight": "bold"}
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
            # Slide 3: Organisation (Organigramm)
            {
                "layout": "content",
                "elements": [
                    {
                        "type": "text",
                        "content": "Organisationsstruktur",
                        "position": {"x": 50, "y": 30},
                        "size": {"width": 700, "height": 50},
                        "properties": {"font_size": 32, "font_weight": "bold"}
                    },
                    {
                        "type": "org_chart",
                        "levels": [
                            ["Umweltbehörde Brandenburg"],
                            ["Immissionsschutz", "Naturschutz", "Gewässerschutz"],
                            ["BImSchG", "Lärm", "Flora", "Fauna", "Wasser", "Boden"]
                        ],
                        "position": {"x": 50, "y": 100}
                    }
                ]
            },
            # Slide 4: Verbesserungsprozess (PDCA)
            {
                "layout": "content",
                "elements": [
                    {
                        "type": "text",
                        "content": "Kontinuierliche Verbesserung",
                        "position": {"x": 50, "y": 30},
                        "size": {"width": 700, "height": 50},
                        "properties": {"font_size": 32, "font_weight": "bold", "align": "center"}
                    },
                    {
                        "type": "cycle_diagram",
                        "steps": ["Plan", "Do", "Check", "Act"],
                        "position": {"x": 400, "y": 300}
                    }
                ]
            }
        ]
    }
    
    slides = await agent._render_slides(vdl)
    pptx_path = agent._create_pptx(vdl, slides)
    
    print(f"✅ Komplette Präsentation erstellt!")
    print(f"   Folien: {len(slides)}")
    print(f"   PPTX: {pptx_path}")
    print(f"   → Slide 1: Titelfolie")
    print(f"   → Slide 2: Flowchart (Genehmigungsprozess)")
    print(f"   → Slide 3: Organigramm (Organisation)")
    print(f"   → Slide 4: Zyklisches Diagramm (PDCA)")
    print(f"\n   🎉 Alle Shapes sind EDITIERBAR in PowerPoint!")


async def main():
    """Führt alle Demos aus"""
    print("\n" + "="*60)
    print("PowerPoint-Präsentationen - Shapes & Diagrams Demo")
    print("VERITAS Presentation Canvas Agent")
    print("="*60)
    
    # Demo 1: Basis-Formen
    await demo_1_basic_shapes()
    
    # Demo 2: Flowchart
    await demo_2_flowchart()
    
    # Demo 3: Organigramm
    await demo_3_org_chart()
    
    # Demo 4: Zyklisches Diagramm
    await demo_4_cycle_diagram()
    
    # Demo 5: Komplette Präsentation
    await demo_5_complete_presentation()
    
    print("\n" + "="*60)
    print("✅ ALLE DEMOS ERFOLGREICH!")
    print("="*60)
    print("\nNächste Schritte:")
    print("1. Öffne die erstellten PPTX-Dateien in PowerPoint")
    print("2. Bearbeite die Shapes (sie sind native PowerPoint-Objekte!)")
    print("3. Passe Farben, Texte, Positionen an")
    print("4. Nutze PowerPoint-Features (Animationen, Übergänge, etc.)")
    print("\n💡 Tipp: Setze 'use_native_shapes': true für editierbare Shapes!")


if __name__ == '__main__':
    asyncio.run(main())
