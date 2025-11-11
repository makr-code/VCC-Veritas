"""
VERITAS Wikipedia Agent

Ein spezialisierter Agent für Wikipedia-Abfragen mit umfassenden Suchfunktionen,
Artikelabruf, mehrsprachiger Unterstützung und intelligenter Query-Verarbeitung.

Hauptfunktionen:
- Wikipedia-Artikelsuche und -abruf
- Zusammenfassungen und Volltexte
- Mehrsprachige Unterstützung (de, en, fr, es, etc.)
- Kategorien und Links-Extraktion
- Intelligente Query-Interpretation
- Performance-Caching

Autor: VERITAS Agent System
Datum: 28. September 2025
Version: 1.0.0
"""

import asyncio
import hashlib
import json
import logging
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

# Mock Wikipedia-Module für Demo (wird durch echtes wikipedia Package ersetzt)
try:
    import wikipedia as wiki_module

    WIKIPEDIA_AVAILABLE = True
except ImportError:
    wiki_module = None
    WIKIPEDIA_AVAILABLE = False
    print("⚠️  Wikipedia Package nicht installiert - verwende Mock-Daten")
    print("   Installation: pip install wikipedia")


# =============================================================================
# WIKIPEDIA-SPEZIFISCHE ENUMS UND KONFIGURATION
# =============================================================================


class WikipediaLanguage(Enum):
    """Unterstützte Wikipedia-Sprachen"""

    GERMAN = "de"
    ENGLISH = "en"
    FRENCH = "fr"
    SPANISH = "es"
    ITALIAN = "it"
    DUTCH = "nl"
    RUSSIAN = "ru"
    CHINESE = "zh"
    JAPANESE = "ja"
    PORTUGUESE = "pt"


class WikipediaQueryType(Enum):
    """Wikipedia Query-Typen"""

    SEARCH = "search"  # Suche nach Artikeln
    ARTICLE = "article"  # Spezifischen Artikel abrufen
    SUMMARY = "summary"  # Kurze Zusammenfassung
    CATEGORIES = "categories"  # Artikel-Kategorien
    LINKS = "links"  # Verlinkte Artikel
    RANDOM = "random"  # Zufälliger Artikel
    DISAMBIGUATION = "disambiguation"  # Begriffsklärung


class WikipediaSearchMode(Enum):
    """Wikipedia Suchmodi"""

    TITLE = "title"  # Nur Titel-Suche
    FULLTEXT = "fulltext"  # Volltext-Suche
    SUGGEST = "suggest"  # Suchvorschläge
    EXACT = "exact"  # Exakte Titel-Übereinstimmung


# =============================================================================
# WIKIPEDIA DATENSTRUKTUREN
# =============================================================================


@dataclass
class WikipediaSearchResult:
    """Ein Wikipedia-Suchergebnis"""

    title: str
    summary: str = ""
    url: str = ""
    page_id: Optional[str] = None
    language: str = "de"
    relevance_score: float = 0.0
    disambiguation: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WikipediaArticle:
    """Ein vollständiger Wikipedia-Artikel"""

    title: str
    content: str
    summary: str
    url: str
    page_id: Optional[str] = None
    language: str = "de"

    # Metadaten
    categories: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)

    # Statistiken
    word_count: int = 0
    section_count: int = 0
    last_modified: Optional[str] = None
    view_count: Optional[int] = None

    # Content-Struktur
    sections: Dict[str, str] = field(default_factory=dict)
    infobox: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def get_section(self, section_name: str) -> Optional[str]:
        """Spezifischen Abschnitt abrufen"""
        return self.sections.get(section_name)

    def get_summary_sentences(self, count: int = 3) -> str:
        """Erste n Sätze der Zusammenfassung"""
        sentences = self.summary.split(". ")
        return ". ".join(sentences[:count]) + ("." if len(sentences) > count else "")


@dataclass
class WikipediaCategory:
    """Wikipedia-Kategorie-Information"""

    name: str
    articles_count: int = 0
    subcategories: List[str] = field(default_factory=list)
    parent_categories: List[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# WIKIPEDIA QUERY REQUEST/RESPONSE
# =============================================================================


@dataclass
class WikipediaQueryRequest:
    """Wikipedia Query Request"""

    query_id: str
    query_text: str

    # Wikipedia-spezifisch
    query_type: WikipediaQueryType = WikipediaQueryType.SEARCH
    language: WikipediaLanguage = WikipediaLanguage.GERMAN
    search_mode: WikipediaSearchMode = WikipediaSearchMode.TITLE

    # Parameter
    max_results: int = 10
    include_summary: bool = True
    include_content: bool = False
    include_links: bool = False
    include_categories: bool = False
    include_images: bool = False

    # Filterung
    min_word_count: int = 0
    exclude_disambiguation: bool = False
    only_featured_articles: bool = False

    # Suche
    search_terms: List[str] = field(default_factory=list)
    exact_title: Optional[str] = None
    category_filter: Optional[str] = None

    def __post_init__(self):
        """Post-initialization processing"""
        if not self.search_terms and self.query_text:
            # Extrahiere Suchbegriffe aus Query-Text
            self.search_terms = self._extract_search_terms(self.query_text)

    def _extract_search_terms(self, text: str) -> List[str]:
        """Extrahiere Suchbegriffe aus natürlichsprachigem Text"""
        # Entferne Stopp-Wörter und extrahiere relevante Begriffe
        stop_words = {
            "der",
            "die",
            "das",
            "und",
            "oder",
            "aber",
            "in",
            "auf",
            "für",
            "von",
            "mit",
            "zu",
            "an",
            "aus",
            "bei",
            "nach",
            "vor",
            "über",
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "for",
            "of",
            "with",
            "to",
            "was",
            "ist",
            "sind",
            "war",
            "waren",
            "what",
            "who",
            "where",
            "when",
        }

        # Einfache Wort-Extraktion (kann verbessert werden)
        words = re.findall(r"\b[a-zA-ZäöüÄÖÜß]+\b", text.lower())
        search_terms = [w for w in words if w not in stop_words and len(w) > 2]

        return search_terms[:5]  # Maximal 5 Suchbegriffe

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["query_type"] = self.query_type.value
        result["language"] = self.language.value
        result["search_mode"] = self.search_mode.value
        return result


@dataclass
class WikipediaQueryResponse:
    """Wikipedia Query Response"""

    query_id: str
    success: bool

    # Results
    search_results: List[WikipediaSearchResult] = field(default_factory=list)
    articles: List[WikipediaArticle] = field(default_factory=list)
    categories: List[WikipediaCategory] = field(default_factory=list)

    # Metadata
    total_results: int = 0
    results_returned: int = 0
    search_terms_used: List[str] = field(default_factory=list)
    language_used: str = "de"
    query_type_used: str = "search"

    # Performance
    processing_time_ms: int = 0
    api_calls_made: int = 0
    cache_hits: int = 0

    # Quality
    confidence_score: float = 0.0
    disambiguation_suggestions: List[str] = field(default_factory=list)
    related_topics: List[str] = field(default_factory=list)

    # Error handling
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["search_results"] = [r.to_dict() for r in self.search_results]
        result["articles"] = [a.to_dict() for a in self.articles]
        result["categories"] = [c.to_dict() for c in self.categories]
        return result

    def get_best_result(self) -> Optional[WikipediaSearchResult]:
        """Bestes Suchergebnis (höchste Relevanz)"""
        if not self.search_results:
            return None
        return max(self.search_results, key=lambda x: x.relevance_score)

    def get_primary_article(self) -> Optional[WikipediaArticle]:
        """Haupt-Artikel (erster/bester)"""
        return self.articles[0] if self.articles else None


# =============================================================================
# WIKIPEDIA AGENT KONFIGURATION
# =============================================================================


@dataclass
class WikipediaConfig:
    """Wikipedia Agent Konfiguration"""

    # Wikipedia-spezifisch
    default_language: str = "de"
    supported_languages: List[str] = field(
        default_factory=lambda: ["de", "en", "fr", "es", "it", "nl", "ru", "zh", "ja", "pt"]
    )
    user_agent: str = "VERITAS Wikipedia Agent/1.0"

    # API-Limits
    max_search_results: int = 50
    max_content_length: int = 10000  # Zeichen
    timeout_seconds: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 0.1

    # Cache-Einstellungen
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600  # 1 Stunde
    max_cache_size: int = 1000

    # Performance
    max_concurrent_requests: int = 5
    min_confidence_threshold: float = 0.7

    # Content-Filter
    exclude_disambiguation_pages: bool = False
    exclude_redirect_pages: bool = False
    min_article_length: int = 100

    # Erweiterte Features
    extract_infobox: bool = True
    extract_categories: bool = True
    extract_links: bool = True
    extract_images: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# WIKIPEDIA AGENT HAUPTKLASSE
# =============================================================================


class WikipediaAgent:
    """
    VERITAS Wikipedia Agent

    Spezialisierter Agent für Wikipedia-Abfragen mit umfassenden Features:
    - Artikelsuche und -abruf
    - Mehrsprachige Unterstützung
    - Intelligente Query-Verarbeitung
    - Performance-Caching
    - Kategorie- und Link-Extraktion
    """

    def __init__(self, config: WikipediaConfig = None):
        self.config = config or WikipediaConfig()
        self.logger = logging.getLogger(f"{__name__}.WikipediaAgent")

        # Caches
        self._search_cache: Dict[str, Any] = {}
        self._article_cache: Dict[str, WikipediaArticle] = {}
        self._category_cache: Dict[str, WikipediaCategory] = {}

        # Performance tracking
        self._stats = {
            "queries_processed": 0,
            "api_calls_made": 0,
            "cache_hits": 0,
            "errors": 0,
            "avg_processing_time_ms": 0,
            "languages_used": set(),
            "total_processing_time_ms": 0,
        }

        # Wikipedia-Setup
        self._setup_wikipedia()

        self.logger.info(f"✅ Wikipedia Agent initialized with language '{self.config.default_language}'")

    def _setup_wikipedia(self):
        """Wikipedia-API Setup"""
        if WIKIPEDIA_AVAILABLE:
            try:
                wiki_module.set_lang(self.config.default_language)
                wiki_module.set_user_agent(self.config.user_agent)
                self.logger.info(f"✅ Wikipedia API configured for language: {self.config.default_language}")
            except Exception as e:
                self.logger.warning(f"Wikipedia API setup warning: {e}")
        else:
            self.logger.info("📝 Using mock Wikipedia data - install 'wikipedia' package for real API access")

    # =========================================================================
    # HAUPT-QUERY-METHODEN (SYNC/ASYNC)
    # =========================================================================

    def execute_query(self, request: WikipediaQueryRequest) -> WikipediaQueryResponse:
        """Synchrone Query-Ausführung"""
        return asyncio.run(self.execute_query_async(request))

    async def execute_query_async(self, request: WikipediaQueryRequest) -> WikipediaQueryResponse:
        """Asynchrone Query-Ausführung (Haupt-Methode)"""
        start_time = time.time()

        try:
            self.logger.info(f"🔍 Processing Wikipedia query: {request.query_text}")

            # Cache-Check
            cache_key = self._generate_cache_key(request)
            if self.config.cache_enabled and cache_key in self._search_cache:
                self.logger.debug("📋 Using cached Wikipedia result")
                self._stats["cache_hits"] += 1
                cached_response = self._search_cache[cache_key]
                cached_response.processing_time_ms = int((time.time() - start_time) * 1000)
                return cached_response

            # Wikipedia-Query basierend auf Typ
            if request.query_type == WikipediaQueryType.SEARCH:
                response = await self._process_search_query(request)
            elif request.query_type == WikipediaQueryType.ARTICLE:
                response = await self._process_article_query(request)
            elif request.query_type == WikipediaQueryType.SUMMARY:
                response = await self._process_summary_query(request)
            elif request.query_type == WikipediaQueryType.CATEGORIES:
                response = await self._process_categories_query(request)
            elif request.query_type == WikipediaQueryType.RANDOM:
                response = await self._process_random_query(request)
            else:
                response = await self._process_search_query(request)  # Default

            # Processing time
            processing_time = int((time.time() - start_time) * 1000)
            response.processing_time_ms = processing_time

            # Stats update
            self._update_stats(processing_time, request.language.value)

            # Cache-Speicherung
            if self.config.cache_enabled and response.success:
                self._search_cache[cache_key] = response
                self._cleanup_cache()

            self.logger.info(f"✅ Wikipedia query completed: {response.results_returned} results in {processing_time}ms")
            return response

        except Exception as e:
            error_msg = f"Wikipedia query error: {str(e)}"
            self.logger.error(error_msg)
            self._stats["errors"] += 1

            return WikipediaQueryResponse(
                query_id=request.query_id,
                success=False,
                error_message=error_msg,
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

    # =========================================================================
    # SPEZIALISIERTE QUERY-VERARBEITUNG
    # =========================================================================

    async def _process_search_query(self, request: WikipediaQueryRequest) -> WikipediaQueryResponse:
        """Verarbeite Suchanfragen"""
        response = WikipediaQueryResponse(
            query_id=request.query_id,
            success=True,
            search_terms_used=request.search_terms,
            language_used=request.language.value,
            query_type_used=request.query_type.value,
        )

        try:
            # Wikipedia-Suche ausführen
            if WIKIPEDIA_AVAILABLE:
                search_results = await self._perform_real_wikipedia_search(request)
            else:
                search_results = self._generate_mock_search_results(request)

            # Ergebnisse verarbeiten und bewerten
            processed_results = []
            for i, result in enumerate(search_results[: request.max_results]):
                wiki_result = WikipediaSearchResult(
                    title=result["title"],
                    summary=result.get("summary", ""),
                    url=result.get(
                        "url", f"https://{request.language.value}.wikipedia.org/wiki/{result['title'].replace(' ', '_')}"
                    ),
                    page_id=result.get("page_id"),
                    language=request.language.value,
                    relevance_score=result.get("relevance_score", 1.0 - (i * 0.1)),  # Absteigende Relevanz
                    disambiguation=result.get("disambiguation", False),
                )
                processed_results.append(wiki_result)

            response.search_results = processed_results
            response.total_results = len(search_results)
            response.results_returned = len(processed_results)

            # Artikel laden wenn angefordert
            if request.include_content and processed_results:
                best_result = processed_results[0]  # Bestes Ergebnis
                article = await self._fetch_article(best_result.title, request.language.value)
                if article:
                    response.articles = [article]

            # Confidence basierend auf Ergebnissen
            if processed_results:
                response.confidence_score = min(0.9, processed_results[0].relevance_score)
            else:
                response.confidence_score = 0.0
                response.warnings.append("Keine Suchergebnisse gefunden")

            return response

        except Exception as e:
            response.success = False
            response.error_message = f"Search processing error: {str(e)}"
            return response

    async def _process_article_query(self, request: WikipediaQueryRequest) -> WikipediaQueryResponse:
        """Verarbeite Artikel-Abfragen"""
        response = WikipediaQueryResponse(
            query_id=request.query_id,
            success=True,
            language_used=request.language.value,
            query_type_used=request.query_type.value,
        )

        try:
            # Artikel-Titel aus Query extrahieren
            title = request.exact_title or request.query_text

            # Artikel laden
            article = await self._fetch_article(title, request.language.value)
            if article:
                response.articles = [article]
                response.results_returned = 1
                response.confidence_score = 0.95
            else:
                response.success = False
                response.error_message = f"Artikel '{title}' nicht gefunden"
                response.confidence_score = 0.0

            return response

        except Exception as e:
            response.success = False
            response.error_message = f"Article processing error: {str(e)}"
            return response

    async def _process_summary_query(self, request: WikipediaQueryRequest) -> WikipediaQueryResponse:
        """Verarbeite Zusammenfassungs-Abfragen"""
        # Erst Suchen, dann Zusammenfassung vom besten Ergebnis
        search_request = WikipediaQueryRequest(
            query_id=request.query_id,
            query_text=request.query_text,
            query_type=WikipediaQueryType.SEARCH,
            language=request.language,
            max_results=1,
            include_summary=True,
        )

        search_response = await self._process_search_query(search_request)

        if search_response.success and search_response.search_results:
            # Konvertiere zu Summary-Response
            result = search_response.search_results[0]

            # Kurze Zusammenfassung erstellen (falls Artikel verfügbar)
            summary_article = WikipediaArticle(
                title=result.title,
                content="",
                summary=result.summary,
                url=result.url,
                page_id=result.page_id,
                language=result.language,
                word_count=len(result.summary.split()),
            )

            return WikipediaQueryResponse(
                query_id=request.query_id,
                success=True,
                articles=[summary_article],
                results_returned=1,
                confidence_score=search_response.confidence_score,
                language_used=request.language.value,
                query_type_used="summary",
                processing_time_ms=search_response.processing_time_ms,
            )
        else:
            return search_response  # Fehlgeschlagene Suche weiterleiten

    async def _process_categories_query(self, request: WikipediaQueryRequest) -> WikipediaQueryResponse:
        """Verarbeite Kategorie-Abfragen"""
        response = WikipediaQueryResponse(
            query_id=request.query_id,
            success=True,
            language_used=request.language.value,
            query_type_used=request.query_type.value,
        )

        try:
            # Mock-Kategorien (in echter Implementierung: Wikipedia-API)
            mock_categories = [
                WikipediaCategory(
                    name="Wissenschaft",
                    articles_count=15420,
                    subcategories=["Physik", "Chemie", "Biologie", "Mathematik"],
                    description="Artikel zu wissenschaftlichen Themen",
                ),
                WikipediaCategory(
                    name="Geschichte",
                    articles_count=8750,
                    subcategories=["Deutsche Geschichte", "Weltgeschichte", "Mittelalter"],
                    description="Historische Artikel und Ereignisse",
                ),
                WikipediaCategory(
                    name="Geographie",
                    articles_count=12300,
                    subcategories=["Städte", "Länder", "Kontinente", "Ozeane"],
                    description="Geographische und topographische Artikel",
                ),
            ]

            response.categories = mock_categories
            response.results_returned = len(mock_categories)
            response.confidence_score = 0.8

            return response

        except Exception as e:
            response.success = False
            response.error_message = f"Categories processing error: {str(e)}"
            return response

    async def _process_random_query(self, request: WikipediaQueryRequest) -> WikipediaQueryResponse:
        """Verarbeite Zufalls-Artikel-Abfragen"""
        import random

        # Mock-Random-Artikel
        random_topics = [
            "Künstliche Intelligenz",
            "Quantencomputer",
            "Klimawandel",
            "Weltgeschichte",
            "Deutsche Literatur",
            "Astronomie",
            "Meeresbiologie",
            "Architektur",
            "Philosophie",
            "Musik",
        ]

        random_title = random.choice(random_topics)

        # Als Artikel-Query weiterleiten
        article_request = WikipediaQueryRequest(
            query_id=request.query_id,
            query_text=random_title,
            query_type=WikipediaQueryType.ARTICLE,
            language=request.language,
            include_content=request.include_content,
            include_summary=request.include_summary,
        )

        return await self._process_article_query(article_request)

    # =========================================================================
    # WIKIPEDIA-API INTEGRATION
    # =========================================================================

    async def _perform_real_wikipedia_search(self, request: WikipediaQueryRequest) -> List[Dict[str, Any]]:
        """Echte Wikipedia-Suche (wenn verfügbar)"""
        if not WIKIPEDIA_AVAILABLE:
            return []

        try:
            # Sprache setzen
            wiki_module.set_lang(request.language.value)

            # Suche ausführen
            search_term = request.exact_title or " ".join(request.search_terms) or request.query_text

            if request.search_mode == WikipediaSearchMode.SUGGEST:
                suggestions = wiki_module.suggest(search_term)
                if suggestions:
                    search_term = suggestions

            # Search-Ergebnisse
            search_results = wiki_module.search(search_term, results=request.max_results)

            results = []
            for title in search_results:
                try:
                    # Summary für jedes Ergebnis
                    summary = wiki_module.summary(title, sentences=3)
                    page = wiki_module.page(title)

                    results.append(
                        {
                            "title": title,
                            "summary": summary,
                            "url": page.url,
                            "page_id": str(page.pageid),
                            "relevance_score": 0.9,  # Kann verbessert werden
                        }
                    )
                except Exception as e:
                    # Skip problematische Artikel
                    self.logger.debug(f"Skipping article '{title}': {e}")
                    continue

            self._stats["api_calls_made"] += 1
            return results

        except Exception as e:
            self.logger.error(f"Real Wikipedia search error: {e}")
            return []

    async def _fetch_article(self, title: str, language: str) -> Optional[WikipediaArticle]:
        """Lade vollständigen Wikipedia-Artikel"""
        cache_key = f"article:{language}:{title}"

        # Cache-Check
        if cache_key in self._article_cache:
            return self._article_cache[cache_key]

        try:
            if WIKIPEDIA_AVAILABLE:
                # Echte Wikipedia-API
                wiki_module.set_lang(language)
                page = wiki_module.page(title)

                article = WikipediaArticle(
                    title=page.title,
                    content=page.content[: self.config.max_content_length],
                    summary=page.summary,
                    url=page.url,
                    page_id=str(page.pageid),
                    language=language,
                    categories=page.categories if self.config.extract_categories else [],
                    links=page.links[:20] if self.config.extract_links else [],  # Limitiert
                    images=page.images[:5] if self.config.extract_images else [],
                    word_count=len(page.content.split()),
                    section_count=len(page.content.split("\n\n")),
                )

                self._stats["api_calls_made"] += 1

            else:
                # Mock-Artikel
                article = self._generate_mock_article(title, language)

            # Cache-Speicherung
            if self.config.cache_enabled:
                self._article_cache[cache_key] = article

            return article

        except Exception as e:
            self.logger.error(f"Article fetch error for '{title}': {e}")
            return None

    # =========================================================================
    # MOCK-DATEN FÜR DEMO (OHNE WIKIPEDIA PACKAGE)
    # =========================================================================

    def _generate_mock_search_results(self, request: WikipediaQueryRequest) -> List[Dict[str, Any]]:
        """Generiere Mock-Suchergebnisse für Demo"""
        query_lower = request.query_text.lower()

        # Verschiedene Mock-Datensätze je nach Query
        mock_results = []

        if any(term in query_lower for term in ["berlin", "deutschland", "german"]):
            mock_results = [
                {
                    "title": "Berlin",
                    "summary": "Berlin ist die Hauptstadt und ein Land der Bundesrepublik Deutschland. Die Stadt ist mit rund 3,7 Millionen Einwohnern die bevölkerungsreichste und mit 892 Quadratkilometern die flächengrößte Gemeinde Deutschlands.",
                    "url": f"https://{request.language.value}.wikipedia.org/wiki/Berlin",
                    "page_id": "3354",
                    "relevance_score": 0.95,
                },
                {
                    "title": "Deutschland",
                    "summary": "Deutschland ist ein Bundesstaat in Mitteleuropa. Er hat 16 Bundesländer und ist als freiheitlich-demokratischer und sozialer Rechtsstaat verfasst.",
                    "url": f"https://{request.language.value}.wikipedia.org/wiki/Deutschland",
                    "page_id": "11867",
                    "relevance_score": 0.85,
                },
            ]
        elif any(term in query_lower for term in ["ki", "artificial", "intelligence", "künstliche"]):
            mock_results = [
                {
                    "title": "Künstliche Intelligenz",
                    "summary": "Künstliche Intelligenz ist ein Teilgebiet der Informatik, das sich mit der Automatisierung intelligenten Verhaltens und dem maschinellen Lernen befasst.",
                    "url": f"https://{request.language.value}.wikipedia.org/wiki/Künstliche_Intelligenz",
                    "page_id": "48749",
                    "relevance_score": 0.92,
                },
                {
                    "title": "Machine Learning",
                    "summary": 'Maschinelles Lernen ist ein Oberbegriff für die „künstliche" Generierung von Wissen aus Erfahrung.',
                    "url": f"https://{request.language.value}.wikipedia.org/wiki/Maschinelles_Lernen",
                    "page_id": "75234",
                    "relevance_score": 0.88,
                },
            ]
        elif any(term in query_lower for term in ["physik", "physics", "wissenschaft"]):
            mock_results = [
                {
                    "title": "Physik",
                    "summary": "Die Physik ist eine Naturwissenschaft, die grundlegende Phänomene der Natur untersucht.",
                    "url": f"https://{request.language.value}.wikipedia.org/wiki/Physik",
                    "page_id": "22980",
                    "relevance_score": 0.90,
                },
                {
                    "title": "Quantenmechanik",
                    "summary": "Die Quantenmechanik ist ein Teilgebiet der Physik, das sich mit den Phänomenen des Mikrokosmos befasst.",
                    "url": f"https://{request.language.value}.wikipedia.org/wiki/Quantenmechanik",
                    "page_id": "25487",
                    "relevance_score": 0.82,
                },
            ]
        else:
            # Allgemeine Mock-Resultate
            mock_results = [
                {
                    "title": f"Artikel zu: {request.query_text}",
                    "summary": f"Dies ist ein Beispielartikel über {request.query_text}. Der Artikel enthält umfassende Informationen zu diesem Thema.",
                    "url": f'https://{request.language.value}.wikipedia.org/wiki/{request.query_text.replace(" ", "_")}',
                    "page_id": f"{hash(request.query_text) % 100000}",
                    "relevance_score": 0.80,
                }
            ]

        return mock_results[: request.max_results]

    def _generate_mock_article(self, title: str, language: str) -> WikipediaArticle:
        """Generiere Mock-Artikel für Demo"""
        # Beispiel-Content basierend auf Titel
        mock_content = f"""
        {title}

        {title} ist ein wichtiges Thema in der entsprechenden Fachdomäne. Dieser Artikel
        bietet eine umfassende Übersicht über alle relevanten Aspekte.

        == Geschichte ==

        Die Geschichte von {title} reicht weit zurück und hat verschiedene Entwicklungsphasen
        durchlaufen. Frühe Entwicklungen fanden bereits im vergangenen Jahrhundert statt.

        == Bedeutung ==

        Die Bedeutung von {title} in der modernen Welt kann nicht überschätzt werden.
        Es spielt eine zentrale Rolle in verschiedenen Bereichen.

        == Aktuelle Entwicklungen ==

        Aktuelle Forschung und Entwicklung zu {title} zeigen vielversprechende Ansätze
        für die Zukunft. Neue Technologien ermöglichen innovative Lösungen.

        == Siehe auch ==

        * Verwandtes Thema A
        * Verwandtes Thema B
        * Weitere Informationen
        """

        summary = (
            f"{title} ist ein wichtiges Thema mit vielfältigen Aspekten und großer Bedeutung in der entsprechenden Fachdomäne."
        )

        return WikipediaArticle(
            title=title,
            content=mock_content.strip(),
            summary=summary,
            url=f"https://{language}.wikipedia.org/wiki/{title.replace(' ', '_')}",
            page_id=str(hash(title) % 100000),
            language=language,
            categories=["Allgemein", "Wissen", "Enzyklopädie"],
            links=[f"Verwandter Artikel zu {title}", "Weitere Informationen", "Ähnliche Themen"],
            word_count=len(mock_content.split()),
            section_count=4,
            sections={
                "Geschichte": "Die Geschichte von " + title + "...",
                "Bedeutung": "Die Bedeutung von " + title + "...",
                "Aktuelle Entwicklungen": "Aktuelle Forschung zu " + title + "...",
            },
        )

    # =========================================================================
    # UTILITY-METHODEN
    # =========================================================================

    def _generate_cache_key(self, request: WikipediaQueryRequest) -> str:
        """Generiere Cache-Schlüssel für Request"""
        key_parts = [
            request.query_text,
            request.query_type.value,
            request.language.value,
            str(request.max_results),
            str(request.include_content),
        ]

    key_string = "|".join(key_parts)
    # Use SHA-256 for cache keys to avoid MD5 (Bandit B324)
    return hashlib.sha256(key_string.encode()).hexdigest()

    def _update_stats(self, processing_time_ms: int, language: str):
        """Update Agent-Statistiken"""
        self._stats["queries_processed"] += 1
        self._stats["total_processing_time_ms"] += processing_time_ms
        self._stats["languages_used"].add(language)

        # Durchschnittliche Processing-Time
        self._stats["avg_processing_time_ms"] = self._stats["total_processing_time_ms"] / self._stats["queries_processed"]

    def _cleanup_cache(self):
        """Cache-Cleanup bei Überlauf"""
        if len(self._search_cache) > self.config.max_cache_size:
            # Entferne 20% der ältesten Einträge
            items_to_remove = len(self._search_cache) // 5
            keys_to_remove = list(self._search_cache.keys())[:items_to_remove]
            for key in keys_to_remove:
                del self._search_cache[key]

    def get_status(self) -> Dict[str, Any]:
        """Agent-Status abrufen"""
        return {
            "agent_type": "wikipedia",
            "version": "1.0.0",
            "status": "active",
            "wikipedia_available": WIKIPEDIA_AVAILABLE,
            "config": self.config.to_dict(),
            "performance": {
                "queries_processed": self._stats["queries_processed"],
                "avg_processing_time_ms": round(self._stats["avg_processing_time_ms"], 2),
                "api_calls_made": self._stats["api_calls_made"],
                "cache_hits": self._stats["cache_hits"],
                "errors": self._stats["errors"],
                "success_rate": (
                    (self._stats["queries_processed"] - self._stats["errors"]) / max(1, self._stats["queries_processed"])
                ),
            },
            "cache": {
                "search_cache_size": len(self._search_cache),
                "article_cache_size": len(self._article_cache),
                "category_cache_size": len(self._category_cache),
            },
            "capabilities": {
                "languages_supported": self.config.supported_languages,
                "languages_used": list(self._stats["languages_used"]),
                "query_types": [qt.value for qt in WikipediaQueryType],
                "search_modes": [sm.value for sm in WikipediaSearchMode],
                "max_results": self.config.max_search_results,
            },
            "timestamp": datetime.now().isoformat(),
        }


# =============================================================================
# FACTORY-FUNKTION
# =============================================================================


def create_wikipedia_agent(config: WikipediaConfig = None) -> WikipediaAgent:
    """Factory-Funktion für Wikipedia Agent"""
    if config is None:
        config = WikipediaConfig()

    agent = WikipediaAgent(config)
    return agent


# =============================================================================
# HAUPTFUNKTION FÜR STANDALONE-TESTING
# =============================================================================


async def main():
    """Hauptfunktion für Testing"""
    print("🔍 VERITAS Wikipedia Agent - Test Suite")
    print("=" * 50)

    # Agent erstellen
    config = WikipediaConfig(default_language="de", max_search_results=5)
    agent = create_wikipedia_agent(config)

    # Test-Queries
    test_queries = [
        {
            "query_text": "Berlin Deutschland Hauptstadt",
            "query_type": WikipediaQueryType.SEARCH,
            "language": WikipediaLanguage.GERMAN,
            "description": "Suche nach Berlin",
        },
        {
            "query_text": "Künstliche Intelligenz",
            "query_type": WikipediaQueryType.ARTICLE,
            "language": WikipediaLanguage.GERMAN,
            "include_content": True,
            "description": "KI-Artikel abrufen",
        },
        {
            "query_text": "Quantencomputer",
            "query_type": WikipediaQueryType.SUMMARY,
            "language": WikipediaLanguage.GERMAN,
            "description": "Quantencomputer Zusammenfassung",
        },
        {
            "query_text": "Random Article",
            "query_type": WikipediaQueryType.RANDOM,
            "language": WikipediaLanguage.GERMAN,
            "description": "Zufälliger Artikel",
        },
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n📋 Test {i}: {query['description']}")
        print(f"   Query: '{query['query_text']}'")

        # Request erstellen
        request = WikipediaQueryRequest(
            query_id=f"test-{i}",
            query_text=query["query_text"],
            query_type=query["query_type"],
            language=query["language"],
            include_content=query.get("include_content", False),
            max_results=3,
        )

        # Query ausführen
        start_time = time.time()
        response = await agent.execute_query_async(request)
        execution_time = int((time.time() - start_time) * 1000)

        # Ergebnisse anzeigen
        if response.success:
            print(f"   ✅ Success: {response.results_returned} results in {execution_time}ms")
            print(f"   📊 Confidence: {response.confidence_score:.2f}")

            # Suchergebnisse
            for result in response.search_results[:2]:  # Nur erste 2
                print(f"      📖 {result.title}")
                print(f"         {result.summary[:100]}...")
                print(f"         🌐 {result.url}")

            # Artikel
            for article in response.articles[:1]:  # Nur erster Artikel
                print(f"      📄 Article: {article.title}")
                print(f"         Words: {article.word_count}, Sections: {article.section_count}")
                print(f"         Categories: {', '.join(article.categories[:3])}")
                if article.content:
                    print(f"         Content preview: {article.content[:150]}...")
        else:
            print(f"   ❌ Error: {response.error_message}")

    # Agent-Status
    print(f"\n📊 Agent Status:")
    status = agent.get_status()
    print(f"   Queries processed: {status['performance']['queries_processed']}")
    print(f"   Avg processing time: {status['performance']['avg_processing_time_ms']:.1f}ms")
    print(f"   Success rate: {status['performance']['success_rate']:.2%}")
    print(f"   Cache hits: {status['performance']['cache_hits']}")
    print(f"   Wikipedia API: {'Available' if status['wikipedia_available'] else 'Mock-Mode'}")

    print("\n✅ Wikipedia Agent test completed!")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Run tests
    asyncio.run(main())
