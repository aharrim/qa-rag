from dataclasses import dataclass
from typing import Any, List, Dict

@dataclass
class ProjectState:
    # dataset
    bugs: List[Dict]

    # analytics
    df: Any
    open_by_component: Any
    resolution_by_component: Any
    open_critical: Any
    open_critical_by_component: Any

    # rag
    collection: Any

    # llm config
    OLLAMA_URL: str
    MODEL: str
