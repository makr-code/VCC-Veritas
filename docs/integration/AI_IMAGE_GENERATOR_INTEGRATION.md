# AI Image Generator - Bildgenerierung & Bildanalyse Integration

**Erstellt:** 3. Dezember 2025
**Version:** 2.0.0
**Status:** ✅ IMPLEMENTIERT

---

## 📋 Übersicht

Der **AI Image Generator** ist ein dualer Agent für:

1. **Bildgenerierung** - Für Präsentationen (VDL Integration)
2. **Bildanalyse** - Für Covina Ingestion & Dokumentverständnis

### Kernfunktionen

**Bildgenerierung:**
- Text-zu-Bild mit Stable Diffusion, DALL-E
- PowerPoint-Integration via VDL
- Multi-Format-Export (PNG, JPEG, WebP)

**Bildanalyse (Vision Models):**
- Bildbeschreibung (Image Captioning)
- OCR (Optical Character Recognition)
- Visual Question Answering (VQA)
- Objekterkennung

---

## 🎨 Bildgenerierung

### Unterstützte Generatoren

| Generator | Beschreibung | Default URL |
|-----------|--------------|-------------|
| **SwarmUI** | Modernes Web-UI für Stable Diffusion | `http://localhost:7801/api` |
| **Stable Diffusion WebUI** | Automatic1111 WebUI | `http://localhost:7860/sdapi/v1` |
| **ComfyUI** | Node-based Workflow System | `http://localhost:8188/api` |
| **DALL-E** | OpenAI API | `https://api.openai.com/v1` |

### SwarmUI - Empfohlen für VERITAS

**Warum SwarmUI?**
- ✅ Moderne UI mit besserer API
- ✅ Unterstützt Bildgenerierung **UND** Bildanalyse
- ✅ LLaVA/BLIP Vision Models integriert
- ✅ Schneller als Automatic1111
- ✅ SDXL-native Unterstützung

**Installation:**
```bash
# SwarmUI installieren
git clone https://github.com/mcmonkeyprojects/SwarmUI
cd SwarmUI
./launch-linux.sh  # oder launch-windows.bat

# Läuft auf http://localhost:7801
```

### Verwendung

```python
from backend.agents.ai_image_generator import AIImageGenerator

# Generator initialisieren
generator = AIImageGenerator(generator_type='swarmui')

# Bild generieren
result = await generator.generate_image(
    prompt="Photorealistic wind turbine farm at sunset, beautiful landscape",
    properties={
        'model': 'sd_xl_base_1.0.safetensors',
        'width': 1024,
        'height': 1024,
        'steps': 30,
        'cfg_scale': 7.5,
        'sampler': 'euler',
        'negative_prompt': 'ugly, blurry, low quality'
    }
)

if result['success']:
    print(f"Bild: {result['image_path']}")
    print(f"Base64: {result['image_base64'][:50]}...")
```

### API-Endpoint

**POST** `/api/images/generate`

```json
{
  "prompt": "Photorealistic wind turbine farm at sunset",
  "generator": "swarmui",
  "properties": {
    "width": 1024,
    "height": 1024,
    "steps": 30,
    "cfg_scale": 7.5,
    "model": "sd_xl_base_1.0.safetensors"
  }
}
```

**Response:**
```json
{
  "success": true,
  "image_path": "/tmp/veritas_images/swarmui_1234567890.png",
  "image_base64": "iVBORw0KGgoAAAANSUhEU...",
  "width": 1024,
  "height": 1024,
  "generator": "swarmui",
  "prompt": "Photorealistic wind turbine farm at sunset"
}
```

---

## 🔍 Bildanalyse (Vision Models)

### Unterstützte Analyse-Tasks

| Task | Beschreibung | Use Case |
|------|--------------|----------|
| **caption** | Bildbeschreibung generieren | Katalogisierung, Präsentationen |
| **ocr** | Text aus Bild extrahieren | Dokumenten-Ingestion, Formulare |
| **vqa** | Visual Question Answering | Interaktive Abfragen |
| **objects** | Objekte erkennen | Diagramm-Analyse, Inventar |

### SwarmUI Vision Models

SwarmUI kann mit folgenden Vision Models arbeiten:

**LLaVA (Large Language-and-Vision Assistant):**
- Bildbeschreibung
- Visual Question Answering
- Multimodales Verständnis

**BLIP/InstructBLIP:**
- Image Captioning
- VQA
- Image-Text Matching

**Konfiguration:**
```bash
# In SwarmUI Settings:
# Models > Download Models > Vision
# - llava-v1.5-13b
# - instructblip-vicuna-13b
# - blip2-opt-6.7b
```

### Verwendung für Covina Ingestion

**Szenario:** PDF mit eingebetteten Bildern/Diagrammen hochladen

```python
from backend.agents.ai_image_generator import AIImageGenerator

generator = AIImageGenerator(generator_type='swarmui')

# OCR auf Dokument-Bild
result = await generator.analyze_image(
    image_path='/path/to/document_page.png',
    task='ocr'
)

if result['success']:
    extracted_text = result['analysis']
    print(f"OCR Text: {extracted_text}")

    # In Covina Ingestion einspeisen
    # → Chromadb Embedding
    # → PostgreSQL Metadaten
```

### API-Endpoints

**POST** `/api/images/analyze`

```json
{
  "image_base64": "iVBORw0KGgoAAAANSUhEU...",
  "task": "ocr",
  "generator": "swarmui"
}
```

**Response:**
```json
{
  "success": true,
  "analysis": "BImSchG-Anlage\nGenehmigung Nr. 12345\nStandort: Brandenburg...",
  "task": "ocr",
  "model": "llava-v1.5-13b",
  "confidence": 0.95
}
```

**POST** `/api/images/analyze/upload` - Mit File-Upload

```bash
curl -X POST http://localhost:5000/api/images/analyze/upload \
  -F "file=@document.jpg" \
  -F "task=ocr" \
  -F "generator=swarmui"
```

**POST** `/api/images/analyze/batch` - Batch-Analyse

```json
[
  {
    "image_path": "/path/to/page1.png",
    "task": "ocr",
    "generator": "swarmui"
  },
  {
    "image_path": "/path/to/page2.png",
    "task": "caption",
    "generator": "swarmui"
  }
]
```

---

## 🔄 Integration mit Covina

### Workflow: Dokument-Ingestion mit Bildanalyse

```
1. PDF/Word Upload
   ↓
2. Extraktion (Text + Bilder)
   ↓
3. Bilder → AI Image Generator
   ↓ (OCR + Caption)
4. OCR-Text + Bildbeschreibung
   ↓
5. Chunking & Embedding
   ↓
6. Chromadb + PostgreSQL
   ↓
7. RAG-fähig
```

### Code-Beispiel

```python
from backend.agents.ai_image_generator import AIImageGenerator
import asyncio

async def ingest_document_with_images(pdf_path: str):
    """
    Ingestion-Pipeline mit Bildanalyse
    """
    # 1. PDF → Text + Bilder extrahieren
    from pypdf import PdfReader
    reader = PdfReader(pdf_path)

    # 2. AI Image Generator
    generator = AIImageGenerator(generator_type='swarmui')

    all_content = []

    for page_num, page in enumerate(reader.pages):
        # Text extrahieren
        text = page.extract_text()
        all_content.append({
            'type': 'text',
            'content': text,
            'page': page_num + 1
        })

        # Bilder extrahieren
        if '/XObject' in page['/Resources']:
            for obj in page['/Resources']['/XObject'].values():
                if obj['/Subtype'] == '/Image':
                    # Bild als Base64
                    image_data = obj._data
                    import base64
                    image_base64 = base64.b64encode(image_data).decode('utf-8')

                    # Bildanalyse: OCR + Caption
                    ocr_result = await generator.analyze_image(
                        image_base64=image_base64,
                        task='ocr'
                    )

                    caption_result = await generator.analyze_image(
                        image_base64=image_base64,
                        task='caption'
                    )

                    all_content.append({
                        'type': 'image',
                        'page': page_num + 1,
                        'ocr_text': ocr_result['analysis'],
                        'caption': caption_result['analysis'],
                        'image_base64': image_base64
                    })

    # 3. In Chromadb einpflegen
    # ... Embedding + Speicherung

    return all_content

# Verwendung
asyncio.run(ingest_document_with_images('/path/to/bimschg_doc.pdf'))
```

---

## ⚙️ Konfiguration

### Umgebungsvariablen

```bash
# Generator-Auswahl
AI_IMAGE_GENERATOR=swarmui  # swarmui, stable_diffusion, comfyui, dalle

# URLs
SWARMUI_URL=http://localhost:7801/api
SD_WEBUI_URL=http://localhost:7860/sdapi/v1
COMFYUI_URL=http://localhost:8188/api

# API-Keys (nur für DALL-E/GPT-4 Vision)
AI_IMAGE_API_KEY=sk-...

# Output
VERITAS_IMAGE_DIR=/tmp/veritas_images
```

### .env Beispiel

```bash
# Bildgenerierung & Analyse
AI_IMAGE_GENERATOR=swarmui
SWARMUI_URL=http://192.168.1.100:7801/api
VERITAS_IMAGE_DIR=/data/veritas/images
```

---

## 🧪 Tests

### Test 1: Bildgenerierung

```bash
python backend/agents/ai_image_generator.py
```

**Output:**
```
🎨 Test: swarmui
   Available: True
   ✅ Image generated: /tmp/veritas_images/swarmui_1234.png
      Size: 1024x1024
      Placeholder: False
```

### Test 2: Bildanalyse (OCR)

```python
import asyncio
from backend.agents.ai_image_generator import AIImageGenerator

async def test_ocr():
    generator = AIImageGenerator(generator_type='swarmui')

    result = await generator.analyze_image(
        image_path='/path/to/document.jpg',
        task='ocr'
    )

    print(f"OCR: {result['analysis']}")

asyncio.run(test_ocr())
```

### Test 3: API-Endpoints

```bash
# Health-Check
curl http://localhost:5000/api/images/health/swarmui

# Bildgenerierung
curl -X POST http://localhost:5000/api/images/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Wind turbine farm",
    "generator": "swarmui",
    "properties": {"width": 512, "height": 512}
  }'

# Bildanalyse (Upload)
curl -X POST http://localhost:5000/api/images/analyze/upload \
  -F "file=@test.jpg" \
  -F "task=ocr" \
  -F "generator=swarmui"
```

---

## 📊 Vergleich: Generatoren

| Feature | SwarmUI | SD WebUI | ComfyUI | DALL-E |
|---------|---------|----------|---------|--------|
| **Bildgenerierung** | ✅ | ✅ | ✅ | ✅ |
| **Bildanalyse** | ✅ LLaVA | ✅ CLIP | ❌ | ✅ GPT-4V |
| **OCR** | ✅ | ⚠️ Begrenzt | ❌ | ✅ |
| **On-Premise** | ✅ | ✅ | ✅ | ❌ Cloud |
| **Speed** | ⚡ Schnell | 🐢 Langsam | ⚡ Schnell | 🌐 API |
| **UI** | ✨ Modern | 📊 Komplex | 🔧 Technical | 🌐 API-Only |
| **SDXL** | ✅ Native | ✅ | ✅ | ❌ |
| **Kosten** | 💰 Free | 💰 Free | 💰 Free | 💵 Pay-per-use |

**Empfehlung für VERITAS:** **SwarmUI**
- Dual-Use (Generation + Analysis)
- LLaVA für OCR & Vision
- Schneller als Automatic1111
- Moderne API

---

## 🚀 Roadmap

### Phase 1 (Implementiert): ✅
- Bildgenerierung (SwarmUI, SD, DALL-E)
- Bildanalyse (LLaVA, BLIP, GPT-4V)
- API-Endpoints (Generation + Analysis)
- Covina Integration vorbereitet

### Phase 2 (In Planung):
- ComfyUI Workflow-Integration
- Batch-Processing optimieren
- Cache für häufige Analysen
- Multi-Language OCR (Tesseract Fallback)

### Phase 3 (Zukunft):
- Diagramm-Erkennung & -Rekonstruktion
- Tabellen-Extraktion aus Bildern
- Handschrift-Erkennung
- Video-Frame-Analyse

---

## 💡 Use Cases

### 1. Präsentations-Generierung

```python
# VDL mit AI-Bildern
vdl = {
    "slides": [{
        "elements": [{
            "type": "image",
            "ai_prompt": "Wind turbine farm at sunset",
            "properties": {"ai_generator": "swarmui"}
        }]
    }]
}
```

### 2. Dokumenten-Ingestion

```python
# PDF mit Bildern → OCR → Chromadb
result = await generator.analyze_image(
    image_path='scan.jpg',
    task='ocr'
)
# → Text in RAG-System einspeisen
```

### 3. Katalog-Enrichment

```python
# Produkt-Foto → Beschreibung generieren
result = await generator.analyze_image(
    image_path='product.jpg',
    task='caption'
)
description = result['analysis']
# → Produktkatalog anreichern
```

### 4. Compliance-Checks

```python
# Bauplan → Objekte erkennen
result = await generator.analyze_image(
    image_path='bauplan.jpg',
    task='objects'
)
# → Prüfung gegen Vorschriften
```

---

**Ersteller:** VERITAS Development Team
**Version:** 2.0.0
**Letzte Aktualisierung:** 3. Dezember 2025
**Status:** ✅ Implementiert und getestet

**SwarmUI als duales Werkzeug:**
- ✅ Bildgenerierung für Präsentationen
- ✅ Bildanalyse für Covina Ingestion
- ✅ OCR, Captioning, VQA, Objekterkennung
