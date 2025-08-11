"""
OpenAI API 인터페이스
"""
import os
from typing import List

try:
    from openai import OpenAI
except Exception:
    raise SystemExit("openai SDK not found. Run: pip install openai")

from config import ASR_MODEL, LLM_MODEL


class OpenAIHelper:
    """OpenAI API를 사용한 음성 인식 및 텍스트 생성"""
    
    def __init__(self):
        if not os.getenv("OPENAI_API_KEY"):
            raise SystemExit("OPENAI_API_KEY not set.")
        self.client = OpenAI()

    def transcribe(self, wav_path: str) -> str:
        """WAV 파일을 텍스트로 변환 (Whisper 사용, 한국어 명시)"""
        with open(wav_path, "rb") as f:
            try:
                result = self.client.audio.transcriptions.create(
                    model=ASR_MODEL,
                    file=f,
                    response_format="text",
                    language="ko",  # 한국어 명시적 지정
                    prompt="한국어로 말하고 있습니다. 게임에서 사용하는 일상적인 단어들입니다.",  # 한국어 컨텍스트 제공
                    temperature=0,
                )
                return (result or "").strip()
            except Exception as e:
                return f"__error__: {e}"
    
    def transcribe_audio_data(self, audio_data: bytes, filename: str = "audio.wav") -> str:
        """오디오 바이너리 데이터를 직접 텍스트로 변환 (파일 저장 불필요)"""
        try:
            from io import BytesIO
            
            # 디버깅: 오디오 데이터 크기 확인
            print(f"오디오 데이터 크기: {len(audio_data)} bytes")
            
            if len(audio_data) < 5000:  # 더 큰 임계값 (5KB 미만은 거부)
                return "음성이 너무 짧거나 조용합니다. 더 크고 길게 말해주세요."
            
            audio_file = BytesIO(audio_data)
            audio_file.name = filename  # 파일명 지정 (확장자로 포맷 인식)
            
            result = self.client.audio.transcriptions.create(
                model=ASR_MODEL,
                file=audio_file,
                response_format="verbose_json",  # 더 상세한 결과
                language="ko",  # 한국어 명시적 지정
                prompt="",  # 프롬프트 제거 (편향 방지)
                temperature=0.3,  # 약간의 랜덤성 추가
            )
            
            # verbose_json에서 텍스트 추출
            transcription = ""
            if hasattr(result, 'text'):
                transcription = result.text.strip()
            elif isinstance(result, dict) and 'text' in result:
                transcription = result['text'].strip()
            else:
                transcription = str(result).strip()
                
            print(f"음성 인식 결과: '{transcription}'")
            
            # 유튜브 관련 잘못된 인식 결과만 간단히 필터링
            if transcription and self._is_youtube_garbage(transcription):
                print(f"유튜브 관련 잘못된 인식으로 판단: '{transcription}'")
                return "음성 인식 결과가 명확하지 않습니다. 다시 말해주세요."
            
            if not transcription:
                return "음성 인식 결과가 없습니다. 더 명확하게 말해주세요."
            
            return transcription
            
            # 이상한 결과 필터링
            strange_responses = [
                "시청해주셔서 감사합니다",
                "시청해 주셔서 감사합니다", 
                "감사합니다",
                "안녕하세요",
                "구독",
                "좋아요",
                "thank you",
                "thanks"
            ]
            
            if transcription.lower() in [s.lower() for s in strange_responses]:
                print(f"이상한 응답 감지됨: '{transcription}' - 무시합니다")
                return "음성 인식 결과가 명확하지 않습니다. 다시 말해주세요."
            
            if not transcription:
                return "음성 인식 결과가 없습니다. 더 명확하게 말해주세요."
            
            return transcription
            
        except Exception as e:
            print(f"음성 인식 오류: {e}")
            return f"__error__: {e}"
    
    def _is_youtube_garbage(self, text: str) -> bool:
        """유튜브 관련 잘못된 인식인지 확인 (정확한 매칭만)"""
        youtube_patterns = [
            "시청해주셔서 감사합니다",
            "시청해 주셔서 감사합니다", 
            "구독해주세요",
            "좋아요 눌러주세요",
            "알림 설정",
            "다음 영상에서",
            "이전 영상에서",
        ]
        
        text_clean = text.strip().lower().replace(" ", "")
        
        # 정확한 매칭만 (부분 문자열이 아닌 완전 매칭)
        for pattern in youtube_patterns:
            pattern_clean = pattern.replace(" ", "").lower()
            if text_clean == pattern_clean:
                return True
        
        return False
    
    def _validate_transcription(self, transcription: str) -> str:
        """AI를 사용해서 음성 인식 결과가 실제 의미있는 내용인지 검증"""
        try:
            validation_prompt = f"""
다음 음성 인식 결과가 실제로 사람이 말한 의미있는 내용인지 판단해주세요.

음성 인식 결과: "{transcription}"

판단 기준:
1. 유튜브 관련 문구 (시청해주셔서 감사합니다, 구독, 좋아요 등)는 거의 확실히 잘못된 인식입니다
2. 완전한 무의미한 문자열도 잘못된 인식입니다  
3. 일상 대화나 게임에서 사용할 수 있는 단어/문장이면 올바른 인식입니다

올바른 인식이면 원본 그대로 반환하고, 잘못된 인식이면 "INVALID"라고만 답변하세요.
"""
            
            resp = self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": validation_prompt}],
                temperature=0.1,
                max_tokens=100
            )
            
            result = (resp.choices[0].message.content or "").strip()
            
            if result == "INVALID":
                return "음성 인식 결과가 명확하지 않습니다. 다시 말해주세요."
            else:
                return transcription
                
        except Exception as e:
            print(f"검증 오류: {e}")
            # 검증 실패시 원본 반환
            return transcription

    def ask_guess(self, history: List[str]) -> str:
        """
        설명 히스토리를 바탕으로 AI가 추측하도록 요청
        규칙: 가능하면 [[word]] 토큰 포함, 한두 문장 이내
        """
        lines = "\n".join(f"- {h}" for h in history[-6:])
        sys = (
            "당신은 추측 게임을 하고 있습니다. 사용자가 금지어를 사용하지 않고 숨겨진 목표어를 설명합니다. "
            "당신은 목표어나 금지어 목록을 볼 수 없습니다.\n"
            "한국어로 간결하게 답변하세요(2문장 이하). 확신이 들면 가장 좋은 추측을 "
            "[[단어]] 형태로 포함하세요(소문자, 공백 없이).\n"
            "예시: 이것은 교통수단 같네요. [[버스]]"
        )
        user = (
            "다음 설명들을 바탕으로 짧은 추론과 함께 답변해주세요. "
            "확신이 들면 [[단어]] 형태로 추측을 포함하세요.\n"
            f"설명들:\n{lines}"
        )
        try:
            resp = self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": sys},
                    {"role": "user", "content": user},
                ],
                temperature=0.2,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:
            return f"(AI error: {e})"
