# vLLM Quick Start - VERITAS

**Schnelleinstieg für vLLM-Integration**

---

## ⚡ In 5 Minuten zu vLLM

### 1️⃣ vLLM Server starten

```bash
# vLLM installieren (einmalig)
pip install vllm

# Server starten mit Llama 3 8B
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3-8B-Instruct \
  --port 8000

# Warten bis "Application startup complete" erscheint
```

### 2️⃣ VERITAS konfigurieren

```bash
# .env Datei bearbeiten (oder neue erstellen)
cat > .env << EOF
LLM_PROVIDER=vllm
VLLM_API_URL=http://localhost:8000
VLLM_DEFAULT_MODEL=meta-llama/Meta-Llama-3-8B-Instruct
EOF
```

### 3️⃣ VERITAS starten

```bash
# Backend starten
python start_backend.py

# In neuem Terminal: Frontend starten
python start_frontend.py
```

### 4️⃣ Testen

Öffne VERITAS UI und stelle eine Frage - läuft jetzt über vLLM! 🎉

---

## 🔄 Zwischen Ollama und vLLM wechseln

### Option 1: Umgebungsvariable

```bash
# Zu vLLM wechseln
export LLM_PROVIDER=vllm

# Zurück zu Ollama
export LLM_PROVIDER=ollama
```

### Option 2: .env Datei

```bash
# Für vLLM
LLM_PROVIDER=vllm

# Für Ollama
LLM_PROVIDER=ollama
```

### Option 3: Im Code

```python
# Explizit vLLM verwenden
from backend.agents.veritas_llm_factory import get_llm_client

client = await get_llm_client(provider="vllm")
```

---

## 🚀 Produktions-Setup

### Docker Compose

```yaml
# docker-compose.vllm.yml
version: '3.8'

services:
  vllm:
    image: vllm/vllm-openai:latest
    ports:
      - "8000:8000"
    environment:
      - MODEL_NAME=meta-llama/Meta-Llama-3-8B-Instruct
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    command: >
      python -m vllm.entrypoints.openai.api_server
      --model ${MODEL_NAME}
      --port 8000
      --host 0.0.0.0

  veritas:
    build: .
    depends_on:
      - vllm
    environment:
      - LLM_PROVIDER=vllm
      - VLLM_API_URL=http://vllm:8000
    ports:
      - "5000:5000"
```

Starten mit:

```bash
docker-compose -f docker-compose.vllm.yml up
```

---

## 🎯 Best Practices

### Entwicklung

- ✅ **Ollama**: Schnelles Setup, lokale Entwicklung
- ✅ **vLLM**: Testing von Produktion-Performance

### Produktion

- ✅ **vLLM**: Besserer Durchsatz, GPU-Optimierung
- ✅ **Automatischer Fallback**: Falls vLLM ausfällt → Ollama

```python
# Automatischer Fallback im Code
from backend.agents.veritas_llm_factory import get_llm_client_with_fallback

client = await get_llm_client_with_fallback()
# Versucht vLLM, fällt zurück auf Ollama wenn nicht verfügbar
```

### Modell-Auswahl

| Use Case | Empfohlenes Modell | Größe |
|----------|-------------------|-------|
| **Schnelle Antworten** | `Llama-3.2-3B-Instruct` | 3B |
| **Standard-Queries** | `Meta-Llama-3-8B-Instruct` | 8B |
| **Komplexe Analysen** | `Mixtral-8x7B-Instruct` | 47B |
| **Höchste Qualität** | `Meta-Llama-3-70B-Instruct` | 70B |

---

## 🐛 Häufige Probleme

### vLLM startet nicht

**Problem:** `CUDA not available`

```bash
# Lösung: CPU-Modus (langsamer, aber funktioniert)
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3-8B-Instruct \
  --device cpu
```

**Problem:** `Out of Memory`

```bash
# Lösung: Kleineres Modell verwenden
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3.2-3B-Instruct
```

### VERITAS findet vLLM nicht

**Problem:** `vLLM Server nicht erreichbar`

```bash
# 1. Prüfen ob vLLM läuft
curl http://localhost:8000/v1/models

# 2. URL in .env prüfen
echo $VLLM_API_URL

# 3. Logs prüfen
python start_backend.py 2>&1 | grep vLLM
```

**Automatischer Fallback:**

```bash
# In .env: Automatisch auf Ollama zurückfallen
LLM_PROVIDER=vllm  # Primär
# Wenn vLLM nicht verfügbar, nutzt System automatisch Ollama
```

### Performance-Probleme

**Problem:** vLLM langsamer als erwartet

```bash
# 1. GPU-Auslastung prüfen
nvidia-smi

# 2. Batch-Size erhöhen (vLLM server)
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3-8B-Instruct \
  --max-num-seqs 32  # Standard: 256, höher = mehr parallele Requests

# 3. Tensor-Parallelismus nutzen (multi-GPU)
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3-70B-Instruct \
  --tensor-parallel-size 4  # 4 GPUs
```

---

## 📊 Performance-Monitoring

### Statistiken abrufen

```python
from backend.agents.veritas_llm_factory import get_llm_client

client = await get_llm_client()
stats = client.get_client_statistics()

print(f"Provider: {stats['client_info']['provider']}")
print(f"Requests: {stats['usage_stats']['requests_successful']}")
print(f"Avg Response Time: {stats['usage_stats']['average_response_time']:.2f}s")
print(f"Total Tokens: {stats['usage_stats']['total_tokens']}")
```

### Logs aktivieren

```python
import logging
logging.basicConfig(level=logging.INFO)

# Nur vLLM-Logs
logging.getLogger('backend.agents.veritas_vllm_client').setLevel(logging.DEBUG)
```

---

## 🔗 Weiterführende Links

- **Vollständige Dokumentation:** [docs/VLLM_INTEGRATION.md](../docs/VLLM_INTEGRATION.md)
- **vLLM Dokumentation:** https://docs.vllm.ai/
- **VERITAS Hauptdoku:** [README.md](../README.md)

---

## ✅ Checkliste für Produktions-Deployment

- [ ] vLLM Server läuft stabil (Health Check grün)
- [ ] GPU-Ressourcen ausreichend (nvidia-smi)
- [ ] Modell geladen und verfügbar (/v1/models)
- [ ] VERITAS .env konfiguriert (LLM_PROVIDER=vllm)
- [ ] Automatischer Fallback zu Ollama konfiguriert
- [ ] Monitoring aktiviert (Logs, Metriken)
- [ ] Load Testing durchgeführt
- [ ] Backup-Strategie definiert

---

**Bei Fragen oder Problemen:** Siehe [VLLM_INTEGRATION.md](../docs/VLLM_INTEGRATION.md) oder Issue erstellen.
