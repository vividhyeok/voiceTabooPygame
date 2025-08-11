"""
Voice Taboo 게임 데이터 모델
"""
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class RoundState:
    """라운드 상태를 나타내는 데이터 클래스"""
    target: str
    forbidden: List[str]
    solved: bool = False
    last_transcription: Optional[str] = None
    feedback: Optional[str] = None
    ai_reply: Optional[str] = None
    ai_guess: Optional[str] = None
    description_history: List[str] = field(default_factory=list)
    taboo_violation: Optional[str] = None
    target_violation: bool = False  # 목표어 말했는지 여부
