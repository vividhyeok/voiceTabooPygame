# 🎮 Voice Taboo - AI 음성 금지어 게임

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-Whisper%20%26%20GPT-green.svg)](https://openai.com)
[![Pygame](https://img.shields.io/badge/Pygame-2.6.1-red.svg)](https://pygame.org)

**8bit 레트로 아케이드 스타일의 AI 음성 인식 금지어 게임**

플레이어가 금지어를 피해서 목표어를 설명하면, AI가 추측하는 혁신적인 음성 게임입니다.

## ✨ 주요 기능

### 🎯 게임 시스템
- **실시간 음성 인식**: OpenAI Whisper를 통한 정확한 한국어 음성 인식
- **AI 추측**: GPT-4o-mini가 설명을 듣고 단어를 추측
- **시간 동결**: 음성 처리 중에는 게임 시간이 정지되어 공정한 플레이
- **두 가지 게임 모드**: 
  - **Time Attack**: 제한 시간 내 최대한 많은 정답
  - **Speed Run**: 목표 개수를 가장 빠르게 달성

### � UI/UX
- **8bit 레트로 아케이드** 스타일 인터페이스
- **네온 효과**와 **픽셀 애니메이션**
- **CRT 모니터** 느낌의 스캔라인 효과
- **아케이드 스타일 메뉴** 시스템

### 📊 데이터 관리
- **플레이어 이름** 시스템
- **모드별 점수 저장** (JSON 파일)
- **실시간 리더보드**
- **103개의 다양한 단어** 데이터베이스

## 🚀 설치 및 실행

### 필수 요구사항
- Python 3.8 이상
- OpenAI API 키
- 마이크가 있는 환경

### 1. 저장소 복제
```bash
git clone https://github.com/yourusername/voice-taboo.git
cd voice-taboo
```

### 2. 패키지 설치
```bash
pip install pygame openai sounddevice numpy python-dotenv
```

### 3. 환경 변수 설정
`.env.example` 파일을 복사해서 `.env` 파일을 만들고 OpenAI API 키를 입력하세요:

```bash
cp .env.example .env
```

`.env` 파일 내용:
```env
OPENAI_API_KEY=your_openai_api_key_here
SAMPLE_RATE=16000
RECORD_SECONDS=3.0
```

### 4. 게임 실행
```bash
python main_arcade.py
```

## 🎮 게임 플레이 방법

### 기본 조작
- **메인 메뉴**: ↑↓ 방향키로 선택, Enter로 확인
- **게임 중**: SPACE 키를 누르고 있는 동안 음성 녹음
- **종료**: ESC 키

### 게임 규칙
1. 화면에 표시된 **목표어**를 AI가 맞추도록 설명하세요
2. **금지어 5개**는 절대 사용하면 안 됩니다
3. **목표어 자체**도 말하면 실패입니다
4. AI가 정답을 맞히면 성공!

### 게임 모드
- **Time Attack**: 60초 동안 최대한 많은 문제 해결
- **Speed Run**: 5개 문제를 가장 빠르게 해결

## 🎮 조작법

- **[방향키]**: 메인 메뉴 내비게이션 (Start Game / Swap Mode / Help)
- **[Enter]**: 메뉴 선택 실행
- **[SPACE]**: 음성 녹음 (누르는 동안 녹음, 떼면 중단)
- **[ESC]**: 게임 종료 / 메인 메뉴로 돌아가기

## 🎯 게임 모드

### TIME ATTACK
- 60초 제한시간 내에 최대한 많은 단어 맞히기
- 성공 시: +10점
- 실패 시: -5점

### SPEED RUN
- 5개 문제를 최대한 빠르게 해결
- 총 소요 시간으로 점수 측정

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/your-username/voice-taboo-game.git
cd voice-taboo-game
```

### 2. 의존성 설치
```bash
pip install pygame sounddevice numpy openai python-dotenv
```

### 3. OpenAI API 키 설정
```bash
# .env 파일 생성
copy .env.example .env

# .env 파일을 열어서 실제 API 키 입력
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 4. 게임 실행
```bash
python main_arcade.py
```

## 📁 프로젝트 구조

```
voice-taboo-game/
├── main_arcade.py           # 메인 실행 파일
├── main_menu.py            # 메인 메뉴 시스템
├── game.py                 # 게임 핵심 로직
├── config.py               # 게임 설정 및 상수
├── models.py               # 데이터 모델
├── utils.py                # 유틸리티 함수
├── openai_helper.py        # OpenAI API 인터페이스
├── taboo_bank.json         # 단어 데이터베이스 (103개 단어)
├── scores_time_attack.json # 타임어택 점수 기록
├── scores_speed_run.json   # 스피드런 점수 기록
├── .env                    # 환경 변수 (생성 필요)
├── .gitignore             # Git 무시 파일
└── README.md              # 프로젝트 문서
```

## ⚙️ 환경 변수 설정

`.env` 파일에서 다음 설정을 커스터마이징할 수 있습니다:

```bash
# 필수 설정
OPENAI_API_KEY=sk-your-api-key-here

# 게임 설정
TABOO_JSON=taboo_bank.json          # 단어 데이터 파일
ROUNDS=5                            # 세션당 라운드 수

# 음성 설정
SAMPLE_RATE=16000                   # 샘플링 레이트
CHUNK_SIZE=1024                     # 오디오 청크 크기

# 게임 모드 설정
TIME_ATTACK_SECONDS=60              # 타임어택 제한시간
SPEED_RUN_TARGET_COUNT=5            # 스피드런 목표 개수

# UI 설정
FONT_NAME=malgun gothic             # 사용할 폰트명
```

## 🎯 단어 데이터베이스

현재 103개의 엄선된 단어가 포함되어 있으며, 각 단어마다 브랜드명과 핵심 키워드가 금지어로 설정되어 있습니다:

- **치킨**: 닭, 튀긴, KFC, 교촌, 굽네치킨, 후라이드 등
- **햄버거**: 맥도날드, 롯데리아, 버거킹, 맘스터치, 패티 등
- **커피**: 아메리카노, 에스프레소, 스타벅스, 이디야, 원두 등

### 새로운 단어 추가
`taboo_bank.json` 파일을 편집하여 새로운 목표어와 금지어를 추가할 수 있습니다:

```json
{"target": "새로운단어", "forbidden": ["금지어1", "금지어2", "금지어3"]}
```

## 🔧 커스터마이징

### 게임 설정 변경
`config.py` 파일에서 다음을 변경할 수 있습니다:
- UI 색상 및 스타일
- 게임 시간 제한
- 점수 계산 방식
- 음성 인식 설정

### 새로운 게임 모드 추가
1. `config.py`에 새로운 모드 추가
2. `models.py`에 모드별 로직 구현
3. `main_menu.py`에 UI 요소 추가

## 🐛 문제 해결

### 한글 깨짐 현상
- Windows: "맑은 고딕" 폰트 자동 사용
- 다른 OS: 시스템에 설치된 한글 폰트로 자동 대체
- 수동 설정: `config.py`의 `FONT_NAME` 수정

### 음성 인식 오류
- 마이크 권한 확인
- 인터넷 연결 상태 확인
- OpenAI API 키 유효성 확인
- 오디오 장치 설정 확인

### API 비용 관리
- 한 게임당 예상 비용: 5,000-7,000원 (KRW)
- Whisper API: ~$0.006/분
- GPT-4o-mini: ~$0.001/질문
- 비용 절약: 짧은 설명 권장

## 📊 API 사용량

### 예상 비용 (한화 기준)
- **타임어택 모드**: 약 5,000-6,000원
- **스피드런 모드**: 약 3,000-4,000원
- **주요 비용**: Whisper API (음성 인식)

### 최적화 팁
- 명확하고 간결한 설명 사용
- 불필요한 배경 소음 제거
- API 키 사용량 모니터링

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## ⚠️ 보안 주의사항

- **절대로** OpenAI API 키를 코드에 직접 입력하지 마세요
- `.env` 파일을 공개 저장소에 커밋하지 마세요
- API 키는 환경 변수로만 관리하세요
- 정기적으로 API 사용량을 모니터링하세요
