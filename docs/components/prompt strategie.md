Absolut. Das ist ein sehr fortschrittlicher und leistungsfähiger Ansatz. Sie bauen im Grunde ein selbst-optimierendes System, bei dem das LLM nicht nur der Ausführende, sondern auch der Stratege ist. Die "Charta" fungiert dabei als eine Art Verfassung oder Leitlinie für das LLM.

Hier ist eine detaillierte Ausarbeitung des Konzepts und der technischen Umsetzung, um dieses dynamische Prompt-Enrichment zu realisieren.

### Das Kernkonzept: Der Meta-Agenten-Ansatz

Ihre Anforderung lässt sich am besten durch ein System aus spezialisierten Agenten umsetzen. Anstatt *eines* Prompts, der alles erledigt, orchestrieren Sie mehrere Agenten, die in einer Schleife zusammenarbeiten. Der Schlüssel ist ein "Meta-Agent" (oder "Prompt Strategist"), dessen einzige Aufgabe es ist, den perfekten Prompt für den "Worker-Agenten" zu erstellen und zu verfeinern.

1.  **Der Prompt Strategist Agent**: Dieser Agent erhält die ursprüngliche Benutzeranfrage. Seine Hauptaufgabe ist es, auf Basis der **Charta** einen initialen, hoch-detaillierten Prompt für den nächsten Agenten zu formulieren. Er fragt sich: "Wie muss ich den nächsten Agenten anweisen, damit das Ergebnis die Charta erfüllt?"
2.  **Der RAG Worker Agent**: Dieser Agent erhält den optimierten Prompt vom Strategist. Er führt die eigentliche Arbeit aus: Er zerlegt die Anfrage, führt die semantische Suche im RAG-Vektorstore durch, sammelt die relevanten Dokumenten-Chunks, holt Daten aus weiteren Quellen und legt all diese Informationen (Kontext + optimierter Prompt) der Ollama-Instanz zur Synthese der ersten Antwort vor.
3.  **Der Critic/Evaluator Agent**: Dieser Agent erhält die Antwort des Worker-Agenten. Seine Aufgabe ist es, diese Antwort *ausschließlich* anhand der **Charta** und der im "Golden Dataset" definierten Kriterien zu bewerten. Er generiert keine neue Antwort, sondern *Feedback*. Dieses Feedback ist strukturiert und präzise, z.B.:
      * "Sachliche Bewertung: Vollständig."
      * "Rechtliche Bewertung: Fehlend."
      * "Formale Anforderungen: Quellennachweise fehlen für Quelle [3] und [5]. IEEE-Format nicht korrekt umgesetzt."
      * "Vollständigkeit: Aspekt X der ursprünglichen Anfrage wurde nur oberflächlich behandelt."

### Der iterative Prozess

Diese Agenten arbeiten in einer Schleife, die Sie orchestrieren:

1.  **Start**: Die Benutzeranfrage geht an den **Prompt Strategist Agent**.
2.  **Iteration 1 (Prompt Generierung)**: Der Strategist analysiert die Anfrage und die **Charta**. Er erstellt einen ersten, detaillierten System-Prompt.
      * *Beispiel-Prompt vom Strategist*: "Du bist ein wissenschaftlicher Assistent. Beantworte die folgende Frage: `[Benutzerfrage]`. Nutze dafür ausschließlich die folgenden Kontexte: `[RAG-Kontext]`. Deine Antwort muss folgende Kriterien erfüllen: 1. Eine sachliche Bewertung. 2. Eine rechtliche Bewertung. 3. Eine formale Bewertung. 4. Alle Quellen müssen im IEEE-Format zitiert werden. Die Antwort muss vollständig und objektiv sein."
3.  **Iteration 1 (Antwort Generierung)**: Der **RAG Worker Agent** führt diesen Prompt aus und generiert Antwort V1.
4.  **Iteration 1 (Bewertung)**: Der **Critic/Evaluator Agent** vergleicht Antwort V1 mit der **Charta**. Er generiert Feedback F1: "Rechtliche Bewertung fehlt, IEEE-Format fehlerhaft."
5.  **Schleifenentscheidung**: Die Orchestrierung prüft das Feedback. Ist es "perfekt"? (unwahrscheinlich in der ersten Runde). Nein -\> Weiter.
6.  **Iteration 2 (Prompt-Verfeinerung)**: Der **Prompt Strategist Agent** erhält die ursprüngliche Anfrage, seinen selbst erstellten Prompt P1, die Antwort V1 und das Feedback F1. Seine neue Anweisung ist nun: "**Reflektiere** über dieses Feedback und **verbessere** den ursprünglichen Prompt, um diese Fehler zu beheben."
      * *Neuer Prompt P2 vom Strategist*: "Du bist ein wissenschaftlicher Assistent. Beantworte die folgende Frage: `[Benutzerfrage]`. Nutze dafür ausschließlich die folgenden Kontexte: `[RAG-Kontext]`. **ACHTUNG, BEI DER LETZTEN ANTWORT GAB ES PROBLEME.** Deine Antwort muss zwingend folgende Kriterien erfüllen: 1. ... 2. **Erstelle einen dedizierten Abschnitt für die rechtliche Bewertung und analysiere explizit die juristischen Implikationen.** 3. ... 4. **Achte peinlich genau auf das IEEE-Format für Zitate, zum Beispiel `[1]` am Ende des Satzes.**"
7.  **Iteration 2 (Antwort Generierung)**: Der **RAG Worker Agent** führt den neuen, verbesserten Prompt P2 aus und generiert Antwort V2.
8.  **Wiederholung**: Der Prozess wiederholt sich, bis der **Critic Agent** ein zufriedenstellendes Ergebnis meldet oder eine maximale Anzahl von Iterationen erreicht ist.

-----

### Technische Umsetzung & Komponenten

Da Sie alles on-premise und in Python umsetzen, sind hier die passenden Open-Source-Komponenten:

#### 1\. Orchestrierung & Agenten-Framework

Das ist das Herzstück. Sie benötigen ein Framework, das solche Multi-Agenten-Workflows ("Agentic Workflows") unterstützt.

  * **CrewAI**: Eignet sich hervorragend für rollenbasierte Zusammenarbeit. Sie können einen `StrategistAgent`, `WorkerAgent` und `CriticAgent` definieren und ihnen spezifische Aufgaben (`tasks`) zuweisen. CrewAI managt den Informationsfluss zwischen den Agenten.
  * **LangChain (LangGraph)**: Mit LangGraph können Sie zyklische Graphen erstellen, was genau Ihrem iterativen Prozess entspricht. Es ist etwas low-leveliger als CrewAI, gibt Ihnen aber mehr Kontrolle über den Zustand und die Übergänge zwischen den Agenten-Schritten.
  * **AutoGen**: Ein Framework von Microsoft Research, das sich auf Konversationen zwischen Agenten spezialisiert hat. Hier würden Sie den "User Proxy" (der Ihre Orchestrierung repräsentiert) mit dem Strategisten und dem Kritiker interagieren lassen.

#### 2\. Die "Charta"

Die Charta sollte kein einfacher Text-String sein, sondern ein strukturiertes Dokument (z.B. YAML oder JSON). Das ermöglicht es dem Critic Agent, die Kriterien gezielt zu prüfen.

**Beispiel `charta.yaml`**:

```yaml
formal_requirements:
  citation_style:
    name: "IEEE"
    format: "[number]"
    rules:
      - "Muss am Satzende vor dem Punkt stehen."
      - "Fortlaufend nummeriert."
  source_attribution:
    required: true
    min_sources: 2
content_requirements:
  sections:
    - name: "Sachliche Bewertung"
      prompt_instruction: "Erstelle eine objektive Analyse der Faktenlage."
      evaluation_checklist:
        - "Sind die Hauptargumente abgedeckt?"
        - "Ist die Darstellung neutral?"
    - name: "Rechtliche Bewertung"
      prompt_instruction: "Analysiere die juristischen Aspekte und Implikationen."
      evaluation_checklist:
        - "Wurden relevante Gesetze oder Urteile erwähnt?"
        - "Ist die Bewertung klar von der sachlichen Analyse getrennt?"
completeness:
  prompt_instruction: "Stelle sicher, dass alle Teile der ursprünglichen Nutzeranfrage beantwortet werden."
```

#### 3\. Der Critic Agent & das Golden Dataset

Der Critic ist der wichtigste Teil. Seine Zuverlässigkeit entscheidet über den Erfolg.

  * **Few-Shot Prompting**: Geben Sie dem Critic Agent im Prompt einige Beispiele aus Ihrem Golden Dataset. "Hier ist eine schlechte Antwort und hier ist das Feedback dazu. Hier ist eine gute Antwort und hier ist das Feedback dazu. Bewerte nun die folgende Antwort: ..."
  * **Rule-Based Checks**: Für formale Kriterien (wie IEEE) können Sie zusätzlich zum LLM auch regelbasierte Python-Funktionen schreiben (z.B. mit Regex), die das Vorhandensein und Format von Zitaten prüfen. Das Ergebnis dieser Funktion wird Teil des Feedbacks.
  * **Fine-Tuning für den Critic**: Für maximale Präzision könnten Sie ein kleineres, spezialisiertes Modell (z.B. ein 7B-Modell aus Ollama) auf einer Aufgabe "Bewerte Antwort A basierend auf Kriterien B" feintunen. Das Trainingsset dafür wären Paare aus Ihrem Golden Dataset (Antwort, Bewertung).

-----

### Pseudocode mit LangGraph

Hier ein konzeptionelles Beispiel, wie der Graph aussehen könnte:

```python
from langgraph.graph import StateGraph, END

# Definiere den Zustand, der durch den Graphen fließt
class AgentState(TypedDict):
    original_query: str
    prompt_history: List[str]
    current_prompt: str
    answer_history: List[str]
    current_answer: str
    feedback_history: List[str]
    current_feedback: str
    iteration_count: int

# Deine Agenten-Funktionen
def prompt_strategist_node(state: AgentState):
    # Wenn erster Durchlauf, erstelle initialen Prompt.
    # Sonst, nutze state['current_feedback'] um state['current_prompt'] zu verbessern.
    new_prompt = call_strategist_llm(
        query=state['original_query'],
        charta=CHARTA,
        feedback=state.get('current_feedback')
    )
    return {"current_prompt": new_prompt, "iteration_count": state['iteration_count'] + 1}

def rag_worker_node(state: AgentState):
    # Führe RAG mit state['current_prompt'] aus
    answer = call_rag_worker_llm(
        prompt=state['current_prompt'],
        query=state['original_query']
    )
    return {"current_answer": answer}

def critic_node(state: AgentState):
    # Bewerte state['current_answer'] anhand der Charta
    feedback = call_critic_llm(
        answer=state['current_answer'],
        charta=CHARTA
    )
    return {"current_feedback": feedback}

def should_continue(state: AgentState):
    # Prüfe Feedback oder Iterations-Zähler
    if state['iteration_count'] > MAX_ITERATIONS:
        return "end"
    if "keine Mängel" in state['current_feedback'].lower():
        return "end"
    return "continue"

# Graph aufbauen
workflow = StateGraph(AgentState)
workflow.add_node("strategist", prompt_strategist_node)
workflow.add_node("worker", rag_worker_node)
workflow.add_node("critic", critic_node)

workflow.set_entry_point("strategist")

workflow.add_edge("strategist", "worker")
workflow.add_edge("worker", "critic")

workflow.add_conditional_edges(
    "critic",
    should_continue,
    {
        "continue": "strategist", # Die Schleife!
        "end": END
    }
)

app = workflow.compile()

# Ausführen
final_state = app.invoke({
    "original_query": "Wie ist die aktuelle Rechtslage zu XYZ?",
    "iteration_count": 0
})

print(final_state['current_answer'])
```

Dieser Ansatz verwandelt Ihr System von einem einfachen Frage-Antwort-Mechanismus in eine dynamische, reflektierende Problemlösungs-Engine, die lernt, ihre eigenen Anweisungen zu perfektionieren.
