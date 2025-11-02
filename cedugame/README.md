# CeduGame - 교육용 게임 플랫폼

다양한 교육용 게임을 제공하는 웹 플랫폼입니다.

## 프로젝트 구조

```
cedugame/
├── index.html          # 메인 게임 선택 페이지
├── games/
│   └── voice-taboo/    # Voice Taboo 게임
│       ├── index.html
│       ├── data/
│       ├── scores_*.json
│       └── 기타 파일들
└── README.md
```

## 게임 목록

### 🎤 Voice Taboo
음성 인식을 활용한 금지어 피하기 게임입니다.

## 개발 노트

### 비용 절감 전략
- 하나의 서버에 총 3개의 게임을 배포할 계획입니다.
- UI 상에서는 각 게임을 따로 표시하지 않고, 링크만 제공하여 간단한 네비게이션 유지.
- 이를 통해 서버 비용을 절감하고, 여러 게임을 효율적으로 관리할 수 있습니다.

## 설치 및 실행

1. 이 리포지토리를 클론합니다.
2. 루트 디렉터리에서 로컬 웹 서버를 실행합니다. (예: `python -m http.server 8080 --directory games/voice-taboo`)
3. 브라우저에서 `http://localhost:8080/index.html`을 열고 게임을 플레이합니다.
	 > **TIP**: `file://` 프로토콜로 직접 열면 환경 변수 파일(`env.txt`)을 불러올 수 없어 Supabase 연동이 비활성화됩니다.

### Supabase / OpenAI 자격 증명 설정

- `games/voice-taboo/env.txt` (커밋 금지)에 다음 값을 채웁니다.

	```dotenv
	OPENAI_API_KEY=...
	SUPABASE_URL=https://xxxx.supabase.co
	SUPABASE_ANON_KEY=ey...
	```

- 또는 같은 내용을 포함한 `env.local.js` 파일을 생성해 다음과 같이 등록할 수 있습니다. (필요 시 `.gitignore`에 추가)

	```js
	window.localEnvConfig = {
			SUPABASE_URL: 'https://xxxx.supabase.co',
			SUPABASE_ANON_KEY: 'ey...',
			OPENAI_API_KEY: 'sk-...'
	};
	```

- 만약 위 파일을 준비하지 못한 경우, 페이지 로드시 표시되는 프롬프트에 Supabase URL과 anon key를 입력하면 브라우저 `localStorage`에 안전하게 저장되어 재사용됩니다.

## 기여

새로운 게임을 추가하려면 `games/` 폴더에 새 폴더를 만들고, 해당 게임의 파일들을 넣으세요. 메인 `index.html`에 게임 카드를 추가하세요.