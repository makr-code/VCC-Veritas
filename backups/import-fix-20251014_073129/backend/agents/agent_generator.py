#!/usr/bin/env python3
"""
VERITAS AGENT GENERATOR
=======================

Automatischer Generator für neue VERITAS Agents basierend auf dem Template

VERWENDUNG:
    python agent_generator.py --domain environmental --capabilities data_analysis,external_api
    
FUNKTIONEN:
- Generiert neue Agent-Dateien aus Template
- Ersetzt Platzhalter mit Domain-spezifischen Werten
- Erstellt Basic Tests und Dokumentation
- Registriert Agent im System

Author: VERITAS System
Date: 2025-09-28
Version: 1.0
"""

import os
import sys
import argparse
import logging
from typing import List, Dict, Any
from pathlib import Path
import shutil
from datetime import datetime

# VERITAS Imports
try:
    from backend.agents.veritas_api_agent_registry import AgentCapability
    AGENT_SYSTEM_AVAILABLE = True
except ImportError:
    AGENT_SYSTEM_AVAILABLE = False

logger = logging.getLogger(__name__)

# ==========================================
# CONFIGURATION
# ==========================================

# Available Agent Domains
AVAILABLE_DOMAINS = [
    "environmental",
    "financial", 
    "legal",
    "medical",
    "educational",
    "construction",
    "traffic",
    "social",
    "security",
    "quality",
    "research",
    "analytics",
    "dwd_weather"  # German Weather Service
]

# Template Mappings
DOMAIN_CONFIGS = {
    "environmental": {
        "description": "Environmental data analysis and monitoring",
        "example_capabilities": ["DATA_ANALYSIS", "EXTERNAL_API_INTEGRATION", "REAL_TIME_PROCESSING"],
        "example_parameters": {
            "api_endpoint": "https://api.openweathermap.org/data/2.5",
            "data_source": "environmental_sensors",
            "model_name": "environmental_classifier"
        }
    },
    "dwd_weather": {
        "description": "German Weather Service (DWD) meteorological data integration",
        "example_capabilities": ["DATA_ANALYSIS", "EXTERNAL_API_INTEGRATION", "REAL_TIME_PROCESSING"],
        "example_parameters": {
            "api_package": "dwdweather2",
            "data_source": "Deutscher Wetterdienst",
            "supported_intervals": ["hourly", "daily"],
            "cache_enabled": True
        }
    },
    "financial": {
        "description": "Financial data processing and analysis",
        "example_capabilities": ["DATA_ANALYSIS", "DOCUMENT_RETRIEVAL", "BATCH_PROCESSING"],
        "example_parameters": {
            "api_endpoint": "https://api.finance-data.com/v1",
            "data_source": "financial_databases",
            "model_name": "financial_analyzer"
        }
    },
    "legal": {
        "description": "Legal document analysis and compliance checking",
        "example_capabilities": ["DOCUMENT_RETRIEVAL", "LLM_INTEGRATION", "QUERY_PROCESSING"],
        "example_parameters": {
            "data_source": "legal_documents",
            "model_name": "legal_llm",
            "api_endpoint": "https://api.legal-db.com"
        }
    }
}

# ==========================================
# AGENT GENERATOR CLASS
# ==========================================

class AgentGenerator:
    """Generator für neue VERITAS Agents"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or os.getcwd())
        self.template_path = self.base_path / "veritas_agent_template.py"
        self.agents_path = self.base_path
        
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template nicht gefunden: {self.template_path}")
    
    def generate_agent(self, 
                      domain: str, 
                      capabilities: List[str] = None,
                      custom_config: Dict[str, Any] = None) -> str:
        """
        Generiert einen neuen Agent aus dem Template
        
        Args:
            domain: Agent Domain (z.B. "environmental")
            capabilities: Liste der Agent Capabilities
            custom_config: Zusätzliche Konfiguration
            
        Returns:
            Pfad zur generierten Agent-Datei
        """
        if domain not in AVAILABLE_DOMAINS:
            raise ValueError(f"Unbekannte Domain: {domain}. Verfügbar: {AVAILABLE_DOMAINS}")
        
        # Generiere Dateinamen
        agent_filename = f"veritas_api_agent_{domain}.py"
        agent_path = self.agents_path / agent_filename
        
        # Template laden
        with open(self.template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Template-Platzhalter ersetzen
        agent_content = self._replace_template_placeholders(
            template_content, domain, capabilities, custom_config
        )
        
        # Agent-Datei schreiben
        with open(agent_path, 'w', encoding='utf-8') as f:
            f.write(agent_content)
        
        logger.info(f"✅ Agent generiert: {agent_path}")
        
        # Test-Datei generieren
        self._generate_test_file(domain, agent_path)
        
        # Dokumentation generieren
        self._generate_documentation(domain, capabilities, custom_config)
        
        return str(agent_path)
    
    def _replace_template_placeholders(self, 
                                     content: str, 
                                     domain: str,
                                     capabilities: List[str] = None,
                                     custom_config: Dict[str, Any] = None) -> str:
        """Ersetzt Template-Platzhalter mit Domain-spezifischen Werten"""
        
        # Basic Replacements
        replacements = {
            "AGENT_DOMAIN = \"template\"": f"AGENT_DOMAIN = \"{domain}\"",
            "template_agent": f"{domain}_agent",
            "TemplateAgent": f"{domain.capitalize()}Agent",
            "Template Agent": f"{domain.capitalize()} Agent",
            "TEMPLATE": domain.upper()
        }
        
        # Capabilities
        if capabilities:
            cap_list = [f"AgentCapability.{cap}" for cap in capabilities]
            cap_string = ",\n    ".join(cap_list)
            replacements["AgentCapability.QUERY_PROCESSING,    # Standard für alle Agents\n    AgentCapability.DATA_ANALYSIS,       # [TEMPLATE] Ersetze mit deinen Capabilities"] = cap_string
        
        # Custom Config
        if custom_config:
            config_lines = []
            for key, value in custom_config.items():
                if isinstance(value, str):
                    config_lines.append(f"    {key}: str = \"{value}\"")
                else:
                    config_lines.append(f"    {key}: Any = {repr(value)}")
            
            if config_lines:
                config_string = "\n".join(config_lines)
                replacements["    # Domain-spezifische Parameter (Beispiele)\n    api_endpoint: Optional[str] = None\n    model_name: Optional[str] = None\n    data_source: Optional[str] = None"] = config_string
        
        # Domain Description
        if domain in DOMAIN_CONFIGS:
            domain_config = DOMAIN_CONFIGS[domain]
            replacements["Template-Implementierung für VERITAS Agent-Worker"] = f"{domain_config['description']} Agent"
        
        # Apply replacements
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        return content
    
    def _generate_test_file(self, domain: str, agent_path: Path):
        """Generiert eine Test-Datei für den Agent"""
        test_filename = f"test_{domain}_agent.py"
        test_path = self.agents_path / "tests" / test_filename
        
        # Tests-Verzeichnis erstellen
        test_path.parent.mkdir(exist_ok=True)
        
        test_content = f'''#!/usr/bin/env python3
"""
Tests für {domain.capitalize()} Agent

Author: VERITAS System
Date: {datetime.now().strftime("%Y-%m-%d")}
"""

import unittest
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.agents.veritas_api_agent_{domain} import (
    {domain.capitalize()}Agent,
    {domain.capitalize()}QueryRequest,
    {domain.capitalize()}QueryResponse,
    {domain.capitalize()}AgentConfig,
    create_{domain}_agent,
    get_default_{domain}_config
)

class Test{domain.capitalize()}Agent(unittest.TestCase):
    
    def setUp(self):
        """Setup für jeden Test"""
        self.config = get_default_{domain}_config()
        self.agent = create_{domain}_agent(self.config)
    
    def tearDown(self):
        """Cleanup nach jedem Test"""
        self.agent.shutdown()
    
    def test_agent_initialization(self):
        """Test Agent Initialisierung"""
        self.assertIsNotNone(self.agent)
        self.assertEqual(self.agent.config, self.config)
        self.assertTrue(self.agent.agent_id.startswith("{domain}_agent_"))
    
    def test_basic_query_processing(self):
        """Test Basic Query Processing"""
        request = {domain.capitalize()}QueryRequest(
            query_id="test-001",
            query_text="Test query for {domain} agent"
        )
        
        response = self.agent.execute_query(request)
        
        self.assertTrue(response.success)
        self.assertEqual(response.query_id, "test-001")
        self.assertGreater(len(response.results), 0)
        self.assertGreater(response.confidence_score, 0)
    
    def test_input_validation(self):
        """Test Input Validation"""
        # Valid request
        valid_request = {domain.capitalize()}QueryRequest(
            query_id="test-002",
            query_text="Valid query"
        )
        self.assertTrue(self.agent.validate_input(valid_request))
        
        # Invalid request (empty query)
        invalid_request = {domain.capitalize()}QueryRequest(
            query_id="test-003",
            query_text=""
        )
        self.assertFalse(self.agent.validate_input(invalid_request))
    
    def test_agent_status(self):
        """Test Agent Status"""
        status = self.agent.get_status()
        
        self.assertIn("agent_id", status)
        self.assertIn("status", status)
        self.assertIn("performance", status)
        self.assertIn("capabilities", status)
    
    def test_capabilities(self):
        """Test Agent Capabilities"""
        capabilities = self.agent.get_capabilities()
        
        self.assertIsInstance(capabilities, list)
        self.assertGreater(len(capabilities), 0)

if __name__ == "__main__":
    unittest.main()
'''
        
        with open(test_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        logger.info(f"✅ Test-Datei generiert: {test_path}")
    
    def _generate_documentation(self, 
                              domain: str, 
                              capabilities: List[str] = None,
                              custom_config: Dict[str, Any] = None):
        """Generiert Dokumentation für den Agent"""
        doc_filename = f"{domain}_agent_README.md"
        doc_path = self.agents_path / "docs" / doc_filename
        
        # Docs-Verzeichnis erstellen
        doc_path.parent.mkdir(exist_ok=True)
        
        # Capabilities formatieren
        cap_list = capabilities or ["QUERY_PROCESSING", "DATA_ANALYSIS"]
        cap_markdown = "\n".join([f"- `{cap}`" for cap in cap_list])
        
        # Config formatieren
        config_markdown = ""
        if custom_config:
            config_lines = [f"- `{key}`: {value}" for key, value in custom_config.items()]
            config_markdown = "\n".join(config_lines)
        
        doc_content = f'''# {domain.capitalize()} Agent

{DOMAIN_CONFIGS.get(domain, {}).get('description', f'Agent für {domain}-spezifische Verarbeitung')}

## Features

- Query-basierte Verarbeitung
- Integriert mit VERITAS Agent-System
- Unterstützt Sync/Async Processing
- Built-in Error Handling und Logging
- Performance Monitoring

## Capabilities

{cap_markdown}

## Konfiguration

{config_markdown if config_markdown else "Standard-Konfiguration verfügbar"}

## Verwendung

```python
from backend.agents.veritas_api_agent_{domain} import create_{domain}_agent

# Agent erstellen
agent = create_{domain}_agent()

# Query ausführen
from backend.agents.veritas_api_agent_{domain} import {domain.capitalize()}QueryRequest

request = {domain.capitalize()}QueryRequest(
    query_id="example-001",
    query_text="Your query here"
)

response = agent.execute_query(request)
print(f"Success: {{response.success}}")
print(f"Results: {{len(response.results)}}")
```

## Tests

```bash
python -m unittest backend.agents.tests.test_{domain}_agent
```

## API

### Query Request

```python
@dataclass
class {domain.capitalize()}QueryRequest:
    query_id: str
    query_text: str
    context: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
```

### Query Response

```python
@dataclass
class {domain.capitalize()}QueryResponse:
    query_id: str
    results: List[Dict[str, Any]]
    success: bool
    confidence_score: float
    processing_time_ms: int
```

## Performance

- Standardmäßig synchrone Verarbeitung
- Async-Support verfügbar
- Integriertes Caching
- Retry-Logic für fehlerhafte Requests

---

*Generiert am: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
*VERITAS Agent System v1.0*
'''
        
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(doc_content)
        
        logger.info(f"✅ Dokumentation generiert: {doc_path}")

# ==========================================
# CLI INTERFACE
# ==========================================

def main():
    """Main CLI Interface"""
    parser = argparse.ArgumentParser(
        description="VERITAS Agent Generator",
        epilog=f"Verfügbare Domains: {', '.join(AVAILABLE_DOMAINS)}"
    )
    
    parser.add_argument(
        "--domain",
        required=True,
        choices=AVAILABLE_DOMAINS,
        help="Agent Domain (z.B. environmental, financial)"
    )
    
    parser.add_argument(
        "--capabilities",
        help="Komma-getrennte Liste von Capabilities (z.B. DATA_ANALYSIS,EXTERNAL_API_INTEGRATION)"
    )
    
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Output-Verzeichnis für generierte Dateien"
    )
    
    parser.add_argument(
        "--config",
        help="JSON-String mit zusätzlicher Konfiguration"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup Logging
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Parse capabilities
    capabilities = None
    if args.capabilities:
        capabilities = [cap.strip().upper() for cap in args.capabilities.split(",")]
    
    # Parse config
    custom_config = None
    if args.config:
        import json
        try:
            custom_config = json.loads(args.config)
        except json.JSONDecodeError as e:
            print(f"❌ Fehler beim Parsen der Konfiguration: {e}")
            return 1
    
    try:
        # Generate Agent
        generator = AgentGenerator(args.output_dir)
        agent_path = generator.generate_agent(
            domain=args.domain,
            capabilities=capabilities,
            custom_config=custom_config
        )
        
        print(f"✅ {args.domain.capitalize()} Agent erfolgreich generiert!")
        print(f"📁 Datei: {agent_path}")
        print(f"🧪 Tests: backend/agents/tests/test_{args.domain}_agent.py")
        print(f"📚 Docs: backend/agents/docs/{args.domain}_agent_README.md")
        print()
        print("🚀 Nächste Schritte:")
        print(f"   1. Implementiere process_query() in {os.path.basename(agent_path)}")
        print(f"   2. Teste mit: python backend/agents/tests/test_{args.domain}_agent.py")
        print(f"   3. Integriere in Agent Registry")
        
        return 0
        
    except Exception as e:
        print(f"❌ Fehler beim Generieren des Agents: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())