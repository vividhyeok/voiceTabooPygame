"""
Voice Taboo 게임 설정 파일
"""
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# -------------------------- Config --------------------------
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))  # 테스트에서 성공한 설정으로 복원
CHANNELS = 1
RECORD_SECONDS = float(os.getenv("RECORD_SECONDS", "3.0"))

# UI 설정
WINDOW_W, WINDOW_H = 980, 640
BG_COLOR = (18, 20, 26)
FG_COLOR = (235, 239, 245)
ACCENT = (120, 193, 255)
MUTED = (130, 140, 155)
GOOD = (80, 200, 120)
BAD = (230, 80, 80)
WARN = (255, 205, 100)

# 한글 지원 폰트 설정
FONT_NAME = os.getenv("FONT_NAME", "malgun gothic")  # Windows에서 한글 지원

# 게임 모드 설정 (time variants – 동일 룰)
TIME_ATTACK_SECONDS = int(os.getenv("TIME_ATTACK_SECONDS", "60"))
SPEED_RUN_TARGET_COUNT = int(os.getenv("SPEED_RUN_TARGET_COUNT", "10"))
SKIP_PENALTY_SECONDS = int(os.getenv("SKIP_PENALTY_SECONDS", "2"))

# OpenAI 설정
ASR_MODEL = "whisper-1"
LLM_MODEL = "gpt-4o-mini"

# 콘텐츠 소스
TABOO_JSON_PATH = os.getenv("TABOO_JSON", "taboo_bank.json")
ROUNDS_PER_SESSION = int(os.getenv("ROUNDS", "12"))

# 내장 fallback 데이터 (JSON 파일이 없을 때)
FALLBACK_TABOO_BANK = [
    {"target": "버스", "forbidden": ["운전", "승객", "자동차", "택시", "급행", "버스"]},
    {"target": "피자", "forbidden": ["치즈", "조각", "이탈리아", "토마토", "페퍼로니", "피자"]},
    {"target": "스마트폰", "forbidden": ["통화", "터치", "화면", "앱", "아이폰", "안드로이드", "스마트폰"]},
]
