"""
VERITAS Frontend - Migration zu Backend v4.0.0
===============================================

Dieses Beispiel zeigt die Änderungen in veritas_app.py
für die Integration des neuen Unified Backend.

ÄNDERUNGEN:
1. Import API Client
2. Initialisierung in __init__
3. send_message() anpassen
4. Source-Parsing aktualisieren
5. Modi vereinfachen
"""

# ============================================================================
# 1. IMPORTS (oben in veritas_app.py einfügen)
# ============================================================================

# NEU: API Client Import
from frontend.api_client import (
    VeritasAPIClient,
    UnifiedResponse,
    SourceMetadata,
    ResponseMetadata
)


# ============================================================================
# 2. INITIALISIERUNG (in VeritasApp.__init__)
# ============================================================================

class VeritasApp:
    """Hauptklasse der VERITAS App"""
    
    def __init__(self, root):
        """Initialisierung"""
        self.root = root
        
        # ... existing code ...
        
        # NEU: API Client initialisieren
        self.api_client = VeritasAPIClient(
            base_url=API_BASE_URL,  # "http://localhost:5000"
            session_id=self.session_id
        )
        logger.info("✅ API Client initialized")
        
        # Health Check beim Start
        try:
            health = self.api_client.health_check()
            if health.get('status') == 'healthy':
                logger.info("✅ Backend healthy")
                components = health.get('components', {})
                logger.info(f"   UDS3: {components.get('uds3', False)}")
                logger.info(f"   Pipeline: {components.get('pipeline', False)}")
            else:
                logger.warning("⚠️  Backend not healthy")
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")


# ============================================================================
# 3. SEND_MESSAGE ANPASSEN (Zeilen ~5940-6100 in veritas_app.py)
# ============================================================================

def send_message(self, message=None, llm=None):
    """
    📤 Sendet Message an Backend v4.0.0
    
    ÄNDERUNGEN:
    - Verwendet api_client.query() statt requests.post()
    - Einheitliche Payload für alle Modi
    - UnifiedResponse mit IEEE Citations
    """
    # ... existing validation code ...
    
    if not message:
        message = self.user_input.get("1.0", "end-1c").strip()
    
    if not message:
        self.add_error_message("Bitte geben Sie eine Frage ein")
        return
    
    if llm is None:
        llm = self.llm_var.get()
    
    # API-Session erstellen falls nicht vorhanden
    if not hasattr(self, 'session_id') or not self.session_id:
        if not self._create_api_session():
            self.add_error_message("Fehler: Keine API-Session verfügbar")
            return
    
    # ===== NEU: Bestimme Query-Modus =====
    mode = "rag"  # Standard
    if hasattr(self, 'current_question_mode') and self.current_question_mode:
        mode = self.current_question_mode.get('key', 'rag')
        logger.info(f"📌 Modus: {mode}")
    
    # ===== NEU: Conversation History =====
    conversation_history = None
    if hasattr(self, 'chat_session') and self.chat_session:
        conversation_history = self._get_conversation_history()
        if conversation_history:
            logger.info(f"📝 Chat-History: {len(conversation_history)} messages")
    
    # Status-Update
    self.api_status_label.config(text="📤")
    self.status_var.set("Sende Nachricht an API...")
    
    try:
        # ===== NEU: API Query via Client =====
        logger.info(f"📤 Query: mode={mode}, model={llm}")
        logger.info(f"   Query: {message[:50]}...")
        
        unified_response: UnifiedResponse = self.api_client.query(
            query=message,
            mode=mode,
            model=llm,
            temperature=self.temperature_var.get() if hasattr(self, 'temperature_var') else 0.7,
            max_tokens=self.max_tokens_var.get() if hasattr(self, 'max_tokens_var') else 2000,
            top_k=5,
            conversation_history=conversation_history
        )
        
        logger.info(f"✅ Response erhalten!")
        logger.info(f"   Sources: {len(unified_response.sources)}")
        logger.info(f"   Duration: {unified_response.metadata.duration:.2f}s")
        
        # ===== NEU: Response verarbeiten =====
        self._process_unified_response(unified_response)
        
        # Status-Update
        self.api_status_label.config(text="✅")
        self.status_var.set(
            f"✅ Antwort erhalten ({unified_response.metadata.duration:.2f}s, "
            f"{len(unified_response.sources)} Quellen)"
        )
        
    except requests.HTTPError as e:
        logger.error(f"❌ API HTTP Error: {e}")
        self.api_status_label.config(text="❌")
        self.status_var.set(f"Fehler: {e.response.status_code if e.response else 'Unknown'}")
        self.add_error_message(f"API-Fehler: {str(e)}")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        self.api_status_label.config(text="❌")
        self.status_var.set("Fehler bei der Verarbeitung")
        self.add_error_message(f"Fehler: {str(e)}")


# ============================================================================
# 4. RESPONSE PROCESSING (NEU)
# ============================================================================

def _process_unified_response(self, response: UnifiedResponse):
    """
    Verarbeitet UnifiedResponse von Backend v4.0.0
    
    Args:
        response: UnifiedResponse mit content, sources, metadata
    """
    # Content extrahieren
    content = response.content
    
    # Sources extrahieren (List[SourceMetadata])
    sources = response.sources
    
    # Metadata extrahieren
    metadata = response.metadata
    
    logger.info(f"📊 Processing Response:")
    logger.info(f"   Content length: {len(content)} chars")
    logger.info(f"   Sources: {len(sources)}")
    logger.info(f"   Model: {metadata.model}")
    logger.info(f"   Mode: {metadata.mode}")
    logger.info(f"   Duration: {metadata.duration:.2f}s")
    logger.info(f"   Tokens: {metadata.tokens_used}")
    
    if metadata.agents_involved:
        logger.info(f"   Agents: {', '.join(metadata.agents_involved)}")
    
    # ===== SOURCES im Detail loggen =====
    if sources:
        logger.info(f"\n📚 Sources Details:")
        for idx, src in enumerate(sources, 1):
            logger.info(f"\n[{src.id}] {src.title}")
            
            # IEEE Fields
            if src.authors:
                logger.info(f"   Authors: {src.authors}")
            if src.ieee_citation:
                logger.info(f"   IEEE: {src.ieee_citation[:100]}...")
            if src.year:
                logger.info(f"   Year: {src.year}")
            
            # Scores
            if src.similarity_score:
                logger.info(f"   Similarity: {src.similarity_score:.2f}")
            if src.rerank_score:
                logger.info(f"   Rerank: {src.rerank_score:.2f}")
            if src.quality_score:
                logger.info(f"   Quality: {src.quality_score:.2f}")
            
            # Assessment
            if src.impact:
                logger.info(f"   Impact: {src.impact}")
            if src.relevance:
                logger.info(f"   Relevance: {src.relevance}")
            
            # Legal
            if src.rechtsgebiet:
                logger.info(f"   Rechtsgebiet: {src.rechtsgebiet}")
            if src.behörde:
                logger.info(f"   Behörde: {src.behörde}")
    
    # ===== UI UPDATE =====
    # Füge Message zur Chat-Anzeige hinzu
    self.add_assistant_message(
        content=content,
        sources=sources,  # List[SourceMetadata]
        metadata=metadata
    )
    
    # Update Source-Panel (falls vorhanden)
    if hasattr(self, '_update_source_panel'):
        self._update_source_panel(sources)


# ============================================================================
# 5. CONVERSATION HISTORY HELPER (NEU)
# ============================================================================

def _get_conversation_history(self) -> Optional[List[Dict[str, str]]]:
    """
    Extrahiert Conversation History für Multi-Turn Queries
    
    Returns:
        List of message dicts mit 'role' und 'content'
        oder None wenn keine History
    """
    if not hasattr(self, 'chat_session') or not self.chat_session:
        return None
    
    if not hasattr(self.chat_session, 'messages'):
        return None
    
    try:
        # Letzte 10 Messages (oder weniger)
        recent_messages = (
            self.chat_session.messages[-10:] 
            if len(self.chat_session.messages) > 10 
            else self.chat_session.messages
        )
        
        # Konvertiere zu API-Format
        history = [
            {
                'role': msg.role,
                'content': msg.content
            }
            for msg in recent_messages
        ]
        
        return history if history else None
        
    except Exception as e:
        logger.warning(f"⚠️  Failed to extract conversation history: {e}")
        return None


# ============================================================================
# 6. ADD_ASSISTANT_MESSAGE ANPASSEN (optional)
# ============================================================================

def add_assistant_message(
    self, 
    content: str, 
    sources: List[SourceMetadata] = None,
    metadata: ResponseMetadata = None
):
    """
    Fügt Assistant-Message zur UI hinzu
    
    Args:
        content: Message Content (Markdown mit [1], [2], [3])
        sources: Liste von SourceMetadata-Objekten
        metadata: ResponseMetadata
    """
    # ... existing message display code ...
    
    # ===== NEU: Source-Details anzeigen =====
    if sources:
        # Erstelle Source-Panel mit IEEE-Details
        source_text = "\n\n📚 **Quellen:**\n\n"
        
        for src in sources:
            source_text += f"**[{src.id}]** {src.title}\n"
            
            # IEEE Citation
            if src.ieee_citation:
                source_text += f"   📖 *{src.ieee_citation}*\n"
            
            # Scores
            scores = []
            if src.similarity_score:
                scores.append(f"Similarity: {src.similarity_score:.2f}")
            if src.rerank_score:
                scores.append(f"Rerank: {src.rerank_score:.2f}")
            if src.quality_score:
                scores.append(f"Quality: {src.quality_score:.2f}")
            
            if scores:
                source_text += f"   📊 {' | '.join(scores)}\n"
            
            # Assessment
            if src.impact or src.relevance:
                assessment = []
                if src.impact:
                    assessment.append(f"Impact: {src.impact}")
                if src.relevance:
                    assessment.append(f"Relevance: {src.relevance}")
                source_text += f"   ⚖️  {' | '.join(assessment)}\n"
            
            # Legal Domain
            if src.rechtsgebiet:
                source_text += f"   ⚖️  Rechtsgebiet: {src.rechtsgebiet}\n"
            
            source_text += "\n"
        
        # Add to display
        # ... (je nach UI-Framework)
    
    # ===== NEU: Metadata anzeigen =====
    if metadata:
        meta_text = "\n\n"
        meta_text += f"🤖 Model: {metadata.model} | "
        meta_text += f"⏱️  {metadata.duration:.2f}s | "
        meta_text += f"🔢 {metadata.tokens_used} tokens\n"
        
        if metadata.agents_involved:
            meta_text += f"🤖 Agents: {', '.join(metadata.agents_involved)}\n"
        
        # Add to display
        # ... (je nach UI-Framework)


# ============================================================================
# 7. MODI VEREINFACHEN (Zeilen ~4490-4560)
# ============================================================================

def _fetch_available_modes(self):
    """
    Holt verfügbare Modi vom Backend v4.0.0
    
    ÄNDERUNGEN:
    - Kein Endpoint-Mapping mehr nötig
    - Alle Modi nutzen /api/query
    - Mode wird als Parameter übergeben
    """
    try:
        # ===== NEU: Hole Modi via API Client =====
        modes_data = self.api_client.get_available_modes()
        
        if modes_data:
            available_modes = []
            
            for mode_key, mode_info in modes_data.items():
                available_modes.append({
                    'key': mode_key,
                    'display': mode_info.get('name', mode_key.upper()),
                    'description': mode_info.get('description', ''),
                    'features': mode_info.get('features', [])
                })
            
            logger.info(f"✅ {len(available_modes)} Modi verfügbar")
            return available_modes
    
    except Exception as e:
        logger.warning(f"⚠️  Failed to fetch modes: {e}")
    
    # ===== FALLBACK: Standard-Modi =====
    logger.warning("⚠️  Using fallback modes")
    return [
        {
            'key': 'rag',
            'display': 'VERITAS RAG',
            'description': 'Retrieval-Augmented Generation',
            'features': ['vector_search', 'agent_orchestration', 'ieee_citations']
        },
        {
            'key': 'hybrid',
            'display': 'Hybrid Search',
            'description': 'BM25 + Dense + RRF Fusion',
            'features': ['keyword_search', 'semantic_search', 'reranking']
        },
        {
            'key': 'agent',
            'display': 'Agent Query',
            'description': 'Multi-Agent Pipeline',
            'features': ['agent_orchestration', 'external_sources']
        },
        {
            'key': 'ask',
            'display': 'Simple Ask',
            'description': 'Direct LLM ohne RAG',
            'features': ['direct_llm', 'fast']
        }
    ]


# ============================================================================
# ZUSAMMENFASSUNG DER ÄNDERUNGEN
# ============================================================================

"""
ÄNDERUNGEN in veritas_app.py:

1. IMPORTS (oben):
   + from frontend.api_client import VeritasAPIClient, UnifiedResponse, SourceMetadata

2. __init__ (Initialisierung):
   + self.api_client = VeritasAPIClient(base_url=API_BASE_URL, session_id=self.session_id)
   + Health Check beim Start

3. send_message() (~Zeilen 5940-6100):
   - Entfernen: endpoint-basierte Logic
   - Entfernen: verschiedene Payloads pro Modus
   + Hinzufügen: mode-Parameter
   + Hinzufügen: api_client.query() Call
   + Hinzufügen: UnifiedResponse Processing

4. NEU: _process_unified_response():
   + Response-Verarbeitung mit IEEE Citations
   + Source-Details Logging
   + UI-Update mit erweiterten Feldern

5. NEU: _get_conversation_history():
   + Multi-Turn Support

6. add_assistant_message():
   + Erweitert um SourceMetadata-Display
   + IEEE-Felder anzeigen
   + Scores, Assessment, Legal Domain

7. _fetch_available_modes() (~Zeilen 4490-4560):
   - Entfernen: Endpoint-Mapping
   + Hinzufügen: api_client.get_available_modes()
   + Vereinfachte Modi-Struktur

ERGEBNIS:
- Alle Queries nutzen /api/query
- Einheitliches UnifiedResponse-Format
- IEEE Citations mit 35+ Feldern
- Einfachere Modi-Verwaltung
"""
