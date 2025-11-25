from dataclasses import dataclass, asdict
from typing import List, Dict
from datetime import datetime, timezone


@dataclass
class AIDocument:
    id: str
    url: str
    title: str
    body_text: str

    word_count: int
    char_count: int
    language: str
    content_type: str

    fetched_at: str

    # Optional / extra signals
    tags: List[str]
    source_domain: str
    path: str
    reading_time_minutes: float
    has_code_blocks: bool
    quality_flags: Dict[str, bool]

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
