#!/usr/bin/env python3
"""
Gap Analysis Script: Veritas Agents vs Mockup Agent Framework
============================================================

Analyzes the current Veritas agent system and compares it with the
mockup agent framework from codespaces-blank to identify:

1. Agent inventory (current Veritas agents)
2. Tool usage patterns
3. Integration complexity
4. Migration priorities
5. Missing capabilities

Usage:
    python scripts/analyze_agent_gap.py

Output:
    - Console report
    - JSON report: reports/agent_gap_analysis.json
    - Markdown report: reports/AGENT_GAP_ANALYSIS.md
"""

import ast
import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from datetime import datetime


@dataclass
class AgentInfo:
    """Information about a Veritas agent."""
    name: str
    file_path: str
    class_name: Optional[str] = None
    methods: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    domain: Optional[str] = None
    line_count: int = 0
    complexity_score: int = 0
    has_tests: bool = False
    mockup_equivalent: Optional[str] = None
    migration_priority: str = "MEDIUM"
    migration_notes: List[str] = field(default_factory=list)


@dataclass
class ToolInfo:
    """Information about a tool used by agents."""
    name: str
    used_by: List[str] = field(default_factory=list)
    usage_count: int = 0
    type: str = "unknown"  # "database", "api", "llm", "search", etc.
    has_openapi_spec: bool = False


@dataclass
class GapAnalysisReport:
    """Complete gap analysis report."""
    timestamp: str
    veritas_agents: List[AgentInfo] = field(default_factory=list)
    mockup_agents: List[str] = field(default_factory=list)
    tools: List[ToolInfo] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class AgentAnalyzer:
    """Analyzes Veritas agent codebase."""
    
    def __init__(self, veritas_root: Path):
        self.veritas_root = veritas_root
        self.agents_dir = veritas_root / "backend" / "agents"
        self.tests_dir = veritas_root / "tests"
        self.mockup_dir = veritas_root / "codespaces-blank" / "agents"
        
        self.agents: List[AgentInfo] = []
        self.tools: Dict[str, ToolInfo] = {}
        
    def analyze(self) -> GapAnalysisReport:
        """Run complete gap analysis."""
        print("🔍 Starting Veritas Agent Gap Analysis...")
        print(f"📁 Veritas root: {self.veritas_root}")
        print(f"📁 Agents directory: {self.agents_dir}")
        print()
        
        # Step 1: Analyze Veritas agents
        print("Step 1: Analyzing Veritas agents...")
        self._analyze_veritas_agents()
        print(f"   ✅ Found {len(self.agents)} Veritas agents")
        print()
        
        # Step 2: Analyze tools
        print("Step 2: Analyzing tool usage...")
        self._analyze_tools()
        print(f"   ✅ Found {len(self.tools)} unique tools")
        print()
        
        # Step 3: Analyze mockup agents
        print("Step 3: Analyzing mockup agents...")
        mockup_agents = self._analyze_mockup_agents()
        print(f"   ✅ Found {len(mockup_agents)} mockup agents")
        print()
        
        # Step 4: Map to mockup equivalents
        print("Step 4: Mapping Veritas → Mockup agents...")
        self._map_to_mockup()
        print(f"   ✅ Mapped agents")
        print()
        
        # Step 5: Calculate migration priorities
        print("Step 5: Calculating migration priorities...")
        self._calculate_priorities()
        print(f"   ✅ Priorities calculated")
        print()
        
        # Step 6: Generate summary
        print("Step 6: Generating summary...")
        summary = self._generate_summary()
        recommendations = self._generate_recommendations()
        print(f"   ✅ Summary generated")
        print()
        
        return GapAnalysisReport(
            timestamp=datetime.now().isoformat(),
            veritas_agents=self.agents,
            mockup_agents=mockup_agents,
            tools=list(self.tools.values()),
            summary=summary,
            recommendations=recommendations
        )
    
    def _analyze_veritas_agents(self):
        """Analyze all Veritas agent files."""
        if not self.agents_dir.exists():
            print(f"⚠️ Agents directory not found: {self.agents_dir}")
            return
        
        # Find all agent files
        agent_files = list(self.agents_dir.glob("veritas_api_agent_*.py"))
        
        for agent_file in agent_files:
            try:
                agent_info = self._analyze_agent_file(agent_file)
                if agent_info:
                    self.agents.append(agent_info)
            except Exception as e:
                print(f"   ⚠️ Error analyzing {agent_file.name}: {e}")
    
    def _analyze_agent_file(self, file_path: Path) -> Optional[AgentInfo]:
        """Analyze a single agent file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"   ⚠️ Could not read {file_path.name}: {e}")
            return None
        
        # Extract agent name from filename
        agent_name = file_path.stem.replace("veritas_api_agent_", "")
        
        # Parse AST
        try:
            tree = ast.parse(content)
        except SyntaxError:
            print(f"   ⚠️ Syntax error in {file_path.name}")
            return None
        
        # Extract information
        class_name = self._extract_class_name(tree)
        methods = self._extract_methods(tree)
        dependencies = self._extract_imports(tree)
        tools_used = self._extract_tools(content)
        domain = self._infer_domain(agent_name, content)
        line_count = len(content.splitlines())
        complexity_score = self._calculate_complexity(tree)
        has_tests = self._check_tests(agent_name)
        
        return AgentInfo(
            name=agent_name,
            file_path=str(file_path.relative_to(self.veritas_root)),
            class_name=class_name,
            methods=methods,
            dependencies=dependencies,
            tools_used=tools_used,
            domain=domain,
            line_count=line_count,
            complexity_score=complexity_score,
            has_tests=has_tests
        )
    
    def _extract_class_name(self, tree: ast.AST) -> Optional[str]:
        """Extract main class name from AST."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Return first class that looks like an agent
                if "Agent" in node.name or "Manager" in node.name:
                    return node.name
        return None
    
    def _extract_methods(self, tree: ast.AST) -> List[str]:
        """Extract method names from AST."""
        methods = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if not item.name.startswith("_"):  # Public methods only
                            methods.append(item.name)
        return methods
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import dependencies."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return imports
    
    def _extract_tools(self, content: str) -> List[str]:
        """Extract tool usage patterns from code."""
        tools = []
        
        # Common patterns
        patterns = {
            "uds3": r"uds3\.|from uds3",
            "ollama": r"ollama\.|OllamaClient",
            "web_search": r"web.*search|WebSearch",
            "database": r"db_manager|database|query",
            "vector_search": r"vector.*search|embedding",
            "bm25": r"bm25|BM25",
            "hybrid_search": r"hybrid.*search|HybridRetriever",
            "llm": r"llm\.|language.*model",
            "api_call": r"requests\.|httpx\.|api",
        }
        
        for tool, pattern in patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                tools.append(tool)
        
        return tools
    
    def _infer_domain(self, agent_name: str, content: str) -> str:
        """Infer domain from agent name and content."""
        domain_keywords = {
            "financial": ["financial", "money", "cost", "budget"],
            "environmental": ["environment", "climate", "weather", "emission"],
            "social": ["social", "community", "people"],
            "construction": ["construction", "building", "architecture"],
            "traffic": ["traffic", "transport", "vehicle"],
            "legal": ["legal", "law", "regulation"],
            "technical": ["technical", "standard", "specification"],
            "orchestration": ["orchestrator", "pipeline", "workflow"],
        }
        
        # Check agent name first
        for domain, keywords in domain_keywords.items():
            if domain in agent_name.lower():
                return domain
        
        # Check content
        for domain, keywords in domain_keywords.items():
            for keyword in keywords:
                if keyword in content.lower():
                    return domain
        
        return "general"
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate complexity score (simple metric)."""
        complexity = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity += 1
            elif isinstance(node, ast.ClassDef):
                complexity += 2
            elif isinstance(node, ast.If):
                complexity += 1
            elif isinstance(node, ast.For) or isinstance(node, ast.While):
                complexity += 1
        
        return complexity
    
    def _check_tests(self, agent_name: str) -> bool:
        """Check if tests exist for this agent."""
        test_patterns = [
            f"test_{agent_name}.py",
            f"test_agent_{agent_name}.py",
            f"test_veritas_agent_{agent_name}.py",
        ]
        
        for pattern in test_patterns:
            test_file = self.tests_dir / pattern
            if test_file.exists():
                return True
        
        return False
    
    def _analyze_tools(self):
        """Analyze tool usage across all agents."""
        tool_types = {
            "uds3": "database",
            "ollama": "llm",
            "web_search": "search",
            "database": "database",
            "vector_search": "search",
            "bm25": "search",
            "hybrid_search": "search",
            "llm": "llm",
            "api_call": "api",
        }
        
        for agent in self.agents:
            for tool in agent.tools_used:
                if tool not in self.tools:
                    self.tools[tool] = ToolInfo(
                        name=tool,
                        type=tool_types.get(tool, "unknown")
                    )
                
                self.tools[tool].used_by.append(agent.name)
                self.tools[tool].usage_count += 1
    
    def _analyze_mockup_agents(self) -> List[str]:
        """Analyze mockup agent framework."""
        mockup_agents = [
            "OrchestratorAgent",
            "DataRetrievalAgent",
            "DataAnalysisAgent",
            "SynthesisAgent",
            "ValidationAgent",
            "TriageAgent",
        ]
        
        # Try to find them in the mockup directory
        if self.mockup_dir.exists():
            agent_files = list(self.mockup_dir.glob("*.py"))
            found_agents = []
            
            for agent_file in agent_files:
                try:
                    with open(agent_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract class names
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            if "Agent" in node.name:
                                found_agents.append(node.name)
                except:
                    pass
            
            if found_agents:
                return found_agents
        
        return mockup_agents
    
    def _map_to_mockup(self):
        """Map Veritas agents to mockup equivalents."""
        mappings = {
            # Orchestration
            "orchestrator": ("OrchestratorAgent", "HIGH", ["Core orchestration - migrate first"]),
            "pipeline_manager": ("OrchestratorAgent", "HIGH", ["Part of core orchestration"]),
            "registry": ("AgentRegistry", "HIGH", ["Core registry - migrate early"]),
            
            # Data Retrieval
            "financial": ("DataRetrievalAgent", "MEDIUM", ["Financial domain retrieval"]),
            "environmental": ("DataRetrievalAgent", "MEDIUM", ["Environmental domain retrieval"]),
            "construction": ("DataRetrievalAgent", "MEDIUM", ["Construction domain retrieval"]),
            "traffic": ("DataRetrievalAgent", "MEDIUM", ["Traffic domain retrieval"]),
            "social": ("DataRetrievalAgent", "MEDIUM", ["Social domain retrieval"]),
            "dwd_weather": ("DataRetrievalAgent", "LOW", ["Weather API - specialized tool"]),
            "wikipedia": ("DataRetrievalAgent", "LOW", ["Wikipedia API - specialized tool"]),
            "chemical_data": ("DataRetrievalAgent", "LOW", ["Chemical data - specialized tool"]),
            "atmospheric_flow": ("DataRetrievalAgent", "LOW", ["Atmospheric - specialized tool"]),
            "technical_standards": ("DataRetrievalAgent", "LOW", ["Standards - specialized tool"]),
            
            # Analysis (if exists)
            # None currently - would be DataAnalysisAgent
            
            # Synthesis (if exists)
            # None currently - would be SynthesisAgent
            
            # Validation (if exists)
            # None currently - would be ValidationAgent
        }
        
        for agent in self.agents:
            agent_key = agent.name.lower()
            
            if agent_key in mappings:
                mockup_equiv, priority, notes = mappings[agent_key]
                agent.mockup_equivalent = mockup_equiv
                agent.migration_priority = priority
                agent.migration_notes = notes
            else:
                # Default mapping
                if agent.domain in ["financial", "environmental", "social", "construction", "traffic"]:
                    agent.mockup_equivalent = "DataRetrievalAgent"
                    agent.migration_priority = "MEDIUM"
                    agent.migration_notes = [f"{agent.domain.capitalize()} domain agent"]
                elif "orchestrat" in agent.name.lower():
                    agent.mockup_equivalent = "OrchestratorAgent"
                    agent.migration_priority = "HIGH"
                    agent.migration_notes = ["Orchestration logic"]
                else:
                    agent.mockup_equivalent = "Unknown"
                    agent.migration_priority = "LOW"
                    agent.migration_notes = ["Needs manual review"]
    
    def _calculate_priorities(self):
        """Calculate migration priorities based on multiple factors."""
        for agent in self.agents:
            score = 0
            notes = []
            
            # High complexity = higher priority (needs refactoring)
            if agent.complexity_score > 50:
                score += 3
                notes.append("High complexity - benefits from framework")
            
            # Many dependencies = higher priority (framework helps)
            if len(agent.dependencies) > 10:
                score += 2
                notes.append("Many dependencies - framework simplifies")
            
            # Core/Orchestration = highest priority
            if agent.domain == "orchestration":
                score += 5
                notes.append("Core orchestration - critical for framework")
            
            # Has tests = can migrate safely
            if agent.has_tests:
                score += 1
                notes.append("Has tests - safer migration")
            else:
                notes.append("⚠️ No tests - add tests before migration")
            
            # Tools used
            if "hybrid_search" in agent.tools_used or "bm25" in agent.tools_used:
                score += 2
                notes.append("Uses Phase 5 - integrate with framework")
            
            # Update priority based on score
            if score >= 8:
                agent.migration_priority = "CRITICAL"
            elif score >= 5:
                agent.migration_priority = "HIGH"
            elif score >= 3:
                agent.migration_priority = "MEDIUM"
            else:
                agent.migration_priority = "LOW"
            
            # Add notes
            agent.migration_notes.extend(notes)
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics."""
        total_agents = len(self.agents)
        total_tools = len(self.tools)
        
        # Count by priority
        priority_counts = defaultdict(int)
        for agent in self.agents:
            priority_counts[agent.migration_priority] += 1
        
        # Count by domain
        domain_counts = defaultdict(int)
        for agent in self.agents:
            domain_counts[agent.domain or "unknown"] += 1
        
        # Count by mockup equivalent
        mockup_counts = defaultdict(int)
        for agent in self.agents:
            mockup_counts[agent.mockup_equivalent or "Unknown"] += 1
        
        # Tool statistics
        most_used_tools = sorted(
            self.tools.values(),
            key=lambda t: t.usage_count,
            reverse=True
        )[:5]
        
        # Complexity statistics
        total_lines = sum(a.line_count for a in self.agents)
        avg_lines = total_lines / total_agents if total_agents > 0 else 0
        total_complexity = sum(a.complexity_score for a in self.agents)
        avg_complexity = total_complexity / total_agents if total_agents > 0 else 0
        
        # Test coverage
        agents_with_tests = sum(1 for a in self.agents if a.has_tests)
        test_coverage = (agents_with_tests / total_agents * 100) if total_agents > 0 else 0
        
        return {
            "total_agents": total_agents,
            "total_tools": total_tools,
            "priority_counts": dict(priority_counts),
            "domain_counts": dict(domain_counts),
            "mockup_mapping": dict(mockup_counts),
            "most_used_tools": [
                {"name": t.name, "usage_count": t.usage_count, "type": t.type}
                for t in most_used_tools
            ],
            "code_statistics": {
                "total_lines": total_lines,
                "avg_lines_per_agent": round(avg_lines, 1),
                "total_complexity": total_complexity,
                "avg_complexity_per_agent": round(avg_complexity, 1),
            },
            "test_coverage": {
                "agents_with_tests": agents_with_tests,
                "percentage": round(test_coverage, 1),
            },
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate migration recommendations."""
        recs = []
        
        # Priority-based recommendations
        critical_agents = [a for a in self.agents if a.migration_priority == "CRITICAL"]
        high_agents = [a for a in self.agents if a.migration_priority == "HIGH"]
        
        if critical_agents:
            recs.append(f"⚠️ CRITICAL: Migrate {len(critical_agents)} critical agents first: {', '.join(a.name for a in critical_agents[:3])}")
        
        if high_agents:
            recs.append(f"🔥 HIGH: Migrate {len(high_agents)} high-priority agents next")
        
        # Test coverage recommendations
        agents_without_tests = [a for a in self.agents if not a.has_tests]
        if agents_without_tests:
            recs.append(f"⚠️ TEST COVERAGE: {len(agents_without_tests)} agents lack tests - add before migration")
        
        # Tool registry recommendations
        if len(self.tools) > 5:
            recs.append(f"📋 TOOL REGISTRY: Create OpenAPI specs for {len(self.tools)} tools")
        
        # Orchestration recommendations
        orchestration_agents = [a for a in self.agents if a.domain == "orchestration"]
        if orchestration_agents:
            recs.append(f"🎯 ORCHESTRATION: Start with {len(orchestration_agents)} orchestration agents (core framework)")
        
        # Complexity recommendations
        complex_agents = [a for a in self.agents if a.complexity_score > 50]
        if complex_agents:
            recs.append(f"🔧 REFACTORING: {len(complex_agents)} complex agents will benefit from framework structure")
        
        # Phase 5 integration
        phase5_agents = [a for a in self.agents if "hybrid_search" in a.tools_used or "bm25" in a.tools_used]
        if phase5_agents:
            recs.append(f"🔍 PHASE 5: {len(phase5_agents)} agents use Phase 5 - integrate with DataRetrievalAgent")
        
        # Domain consolidation
        domain_counts = defaultdict(int)
        for agent in self.agents:
            domain_counts[agent.domain or "unknown"] += 1
        
        if domain_counts.get("general", 0) > 3:
            recs.append(f"📦 CONSOLIDATION: {domain_counts['general']} general agents - consider merging")
        
        return recs


class ReportGenerator:
    """Generate reports from gap analysis."""
    
    def __init__(self, report: GapAnalysisReport, output_dir: Path):
        self.report = report
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_all(self):
        """Generate all report formats."""
        print("📝 Generating reports...")
        
        # JSON report
        json_path = self.output_dir / "agent_gap_analysis.json"
        self._generate_json(json_path)
        print(f"   ✅ JSON: {json_path}")
        
        # Markdown report
        md_path = self.output_dir / "AGENT_GAP_ANALYSIS.md"
        self._generate_markdown(md_path)
        print(f"   ✅ Markdown: {md_path}")
        
        # Console summary
        self._print_summary()
    
    def _generate_json(self, output_path: Path):
        """Generate JSON report."""
        data = {
            "timestamp": self.report.timestamp,
            "summary": self.report.summary,
            "recommendations": self.report.recommendations,
            "agents": [
                {
                    "name": a.name,
                    "file_path": a.file_path,
                    "class_name": a.class_name,
                    "domain": a.domain,
                    "mockup_equivalent": a.mockup_equivalent,
                    "migration_priority": a.migration_priority,
                    "line_count": a.line_count,
                    "complexity_score": a.complexity_score,
                    "has_tests": a.has_tests,
                    "methods": a.methods,
                    "tools_used": a.tools_used,
                    "migration_notes": a.migration_notes,
                }
                for a in self.report.veritas_agents
            ],
            "tools": [
                {
                    "name": t.name,
                    "type": t.type,
                    "usage_count": t.usage_count,
                    "used_by": t.used_by,
                }
                for t in self.report.tools
            ],
            "mockup_agents": self.report.mockup_agents,
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _generate_markdown(self, output_path: Path):
        """Generate Markdown report."""
        md = []
        
        # Header
        md.append("# 🔍 VERITAS AGENT GAP ANALYSIS REPORT")
        md.append("")
        md.append(f"**Generated:** {self.report.timestamp}")
        md.append("")
        md.append("---")
        md.append("")
        
        # Executive Summary
        md.append("## 📊 EXECUTIVE SUMMARY")
        md.append("")
        s = self.report.summary
        md.append(f"- **Total Veritas Agents:** {s['total_agents']}")
        md.append(f"- **Total Tools:** {s['total_tools']}")
        md.append(f"- **Total Lines of Code:** {s['code_statistics']['total_lines']:,}")
        md.append(f"- **Test Coverage:** {s['test_coverage']['percentage']}% ({s['test_coverage']['agents_with_tests']}/{s['total_agents']} agents)")
        md.append("")
        
        # Priority Breakdown
        md.append("### Migration Priority Breakdown")
        md.append("")
        for priority, count in sorted(s['priority_counts'].items(), key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(x[0], 99)):
            emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(priority, "⚪")
            md.append(f"- {emoji} **{priority}:** {count} agents")
        md.append("")
        
        # Recommendations
        md.append("## 💡 RECOMMENDATIONS")
        md.append("")
        for i, rec in enumerate(self.report.recommendations, 1):
            md.append(f"{i}. {rec}")
        md.append("")
        md.append("---")
        md.append("")
        
        # Agent Inventory
        md.append("## 📋 AGENT INVENTORY")
        md.append("")
        
        # Group by priority
        priority_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        for priority in priority_order:
            agents = [a for a in self.report.veritas_agents if a.migration_priority == priority]
            if not agents:
                continue
            
            emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(priority, "⚪")
            md.append(f"### {emoji} {priority} Priority ({len(agents)} agents)")
            md.append("")
            
            for agent in agents:
                md.append(f"#### `{agent.name}`")
                md.append("")
                md.append(f"- **File:** `{agent.file_path}`")
                md.append(f"- **Class:** `{agent.class_name or 'N/A'}`")
                md.append(f"- **Domain:** {agent.domain or 'unknown'}")
                md.append(f"- **Mockup Equivalent:** `{agent.mockup_equivalent or 'Unknown'}`")
                md.append(f"- **Lines of Code:** {agent.line_count}")
                md.append(f"- **Complexity:** {agent.complexity_score}")
                md.append(f"- **Has Tests:** {'✅ Yes' if agent.has_tests else '❌ No'}")
                
                if agent.methods:
                    md.append(f"- **Public Methods ({len(agent.methods)}):** {', '.join(agent.methods[:5])}")
                
                if agent.tools_used:
                    md.append(f"- **Tools Used:** {', '.join(agent.tools_used)}")
                
                if agent.migration_notes:
                    md.append("- **Migration Notes:**")
                    for note in agent.migration_notes:
                        md.append(f"  - {note}")
                
                md.append("")
        
        md.append("---")
        md.append("")
        
        # Tool Inventory
        md.append("## 🛠️ TOOL INVENTORY")
        md.append("")
        md.append("| Tool | Type | Usage Count | Used By |")
        md.append("|------|------|-------------|---------|")
        
        for tool in sorted(self.report.tools, key=lambda t: t.usage_count, reverse=True):
            used_by_str = ", ".join(tool.used_by[:3])
            if len(tool.used_by) > 3:
                used_by_str += f", ... (+{len(tool.used_by) - 3})"
            md.append(f"| `{tool.name}` | {tool.type} | {tool.usage_count} | {used_by_str} |")
        
        md.append("")
        md.append("---")
        md.append("")
        
        # Mockup Mapping
        md.append("## 🗺️ MOCKUP AGENT MAPPING")
        md.append("")
        md.append("| Mockup Agent | Veritas Agents | Count |")
        md.append("|--------------|----------------|-------|")
        
        mockup_to_veritas = defaultdict(list)
        for agent in self.report.veritas_agents:
            if agent.mockup_equivalent:
                mockup_to_veritas[agent.mockup_equivalent].append(agent.name)
        
        for mockup_agent in self.report.mockup_agents:
            veritas_agents = mockup_to_veritas.get(mockup_agent, [])
            agents_str = ", ".join(veritas_agents[:3])
            if len(veritas_agents) > 3:
                agents_str += f", ... (+{len(veritas_agents) - 3})"
            md.append(f"| `{mockup_agent}` | {agents_str or 'None'} | {len(veritas_agents)} |")
        
        md.append("")
        md.append("---")
        md.append("")
        
        # Statistics
        md.append("## 📈 CODE STATISTICS")
        md.append("")
        stats = s['code_statistics']
        md.append(f"- **Total Lines:** {stats['total_lines']:,}")
        md.append(f"- **Average Lines per Agent:** {stats['avg_lines_per_agent']}")
        md.append(f"- **Total Complexity:** {stats['total_complexity']}")
        md.append(f"- **Average Complexity per Agent:** {stats['avg_complexity_per_agent']}")
        md.append("")
        
        # Most Used Tools
        md.append("### 🔝 Most Used Tools")
        md.append("")
        for i, tool in enumerate(s['most_used_tools'], 1):
            md.append(f"{i}. **{tool['name']}** ({tool['type']}) - {tool['usage_count']} uses")
        md.append("")
        
        md.append("---")
        md.append("")
        
        # Next Steps
        md.append("## 🚀 NEXT STEPS")
        md.append("")
        md.append("### Phase 1: Preparation (Week 1)")
        md.append("")
        md.append("1. **Review this report** with team")
        md.append("2. **Create test coverage** for agents without tests")
        md.append("3. **Setup database** (research_plans tables)")
        md.append("4. **Copy schema files** from codespaces-blank")
        md.append("")
        
        md.append("### Phase 2: Core Migration (Week 2-4)")
        md.append("")
        critical_high = [a for a in self.report.veritas_agents if a.migration_priority in ["CRITICAL", "HIGH"]]
        md.append(f"1. **Migrate {len(critical_high)} critical/high priority agents:**")
        for agent in critical_high[:5]:
            md.append(f"   - `{agent.name}` → `{agent.mockup_equivalent}`")
        md.append("")
        
        md.append("### Phase 3: Tools & Registry (Week 5-6)")
        md.append("")
        md.append(f"1. **Create OpenAPI specs** for {len(self.report.tools)} tools")
        md.append("2. **Setup Tool Registry**")
        md.append("3. **Implement access control**")
        md.append("")
        
        md.append("---")
        md.append("")
        md.append("**Report End**")
        
        # Write file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(md))
    
    def _print_summary(self):
        """Print summary to console."""
        print()
        print("=" * 80)
        print("📊 GAP ANALYSIS SUMMARY")
        print("=" * 80)
        print()
        
        s = self.report.summary
        
        print(f"Total Veritas Agents:    {s['total_agents']}")
        print(f"Total Tools:             {s['total_tools']}")
        print(f"Total Lines of Code:     {s['code_statistics']['total_lines']:,}")
        print(f"Test Coverage:           {s['test_coverage']['percentage']}%")
        print()
        
        print("Migration Priority:")
        for priority, count in sorted(s['priority_counts'].items(), key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(x[0], 99)):
            emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(priority, "⚪")
            print(f"  {emoji} {priority:10s}: {count:2d} agents")
        print()
        
        print("Top Recommendations:")
        for i, rec in enumerate(self.report.recommendations[:5], 1):
            print(f"  {i}. {rec}")
        print()
        
        print("=" * 80)
        print()


def main():
    """Main entry point."""
    # Find Veritas root
    script_dir = Path(__file__).parent
    veritas_root = script_dir.parent
    
    print("🚀 Veritas Agent Gap Analysis")
    print(f"📁 Root: {veritas_root}")
    print()
    
    # Run analysis
    analyzer = AgentAnalyzer(veritas_root)
    report = analyzer.analyze()
    
    # Generate reports
    output_dir = veritas_root / "reports"
    generator = ReportGenerator(report, output_dir)
    generator.generate_all()
    
    print()
    print("✅ Gap analysis complete!")
    print(f"📁 Reports saved to: {output_dir}")
    print()
    print("Next steps:")
    print("  1. Review reports/AGENT_GAP_ANALYSIS.md")
    print("  2. Prioritize agent migrations")
    print("  3. Create tests for agents without coverage")
    print("  4. Start Phase 1: Database Setup")
    print()


if __name__ == "__main__":
    main()
