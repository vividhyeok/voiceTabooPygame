"""
Voice Taboo 게임 핵심 로직
"""
import math
import random
import time
import os
from typing import Optional

import pygame
import numpy as np
import sounddevice as sd

from config import (
    WINDOW_W, WINDOW_H, BG_COLOR, FG_COLOR, ACCENT, MUTED, GOOD, BAD, WARN,
    FONT_NAME, TIME_ATTACK_SECONDS, SPEED_RUN_TARGET_COUNT, SKIP_PENALTY_SECONDS,
    SAMPLE_RATE, CHANNELS, ROUNDS_PER_SESSION, RECORD_SECONDS
)
from models import RoundState
from utils import load_taboo_bank, record_block, save_wav_from_array, check_violations, extract_guess_token, start_recording, stop_recording_and_get_audio, audio_array_to_wav_bytes
from openai_helper import OpenAIHelper


class Game:
    """Voice Taboo 게임 메인 클래스"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self._init_fonts()
        self.client = OpenAIHelper()
        self.time_mode = "TIME_ATTACK"  # or "SPEED_RUN"
        self.player_name = "PLAYER"  # 기본 플레이어 이름
        self.reset_session()

    def _init_fonts(self):
        """한글 지원 폰트 초기화"""
        try:
            self.font = pygame.font.SysFont(FONT_NAME, 28)
            self.big = pygame.font.SysFont(FONT_NAME, 42, bold=True)
            self.small = pygame.font.SysFont(FONT_NAME, 22)
        except:
            try:
                self.font = pygame.font.SysFont("gulim", 28)
                self.big = pygame.font.SysFont("gulim", 42, bold=True)
                self.small = pygame.font.SysFont("gulim", 22)
            except:
                self.font = pygame.font.SysFont(None, 28)
                self.big = pygame.font.SysFont(None, 42)
                self.small = pygame.font.SysFont(None, 22)

    def reset_session(self):
        """게임 세션 초기화"""
        bank = load_taboo_bank("taboo_bank.json")
        k = min(ROUNDS_PER_SESSION, len(bank))
        self.items = random.sample(bank, k=k)
        
        self.idx = 0
        self.round: Optional[RoundState] = None
        self.score = 0
        self.start_ts = None
        self.elapsed = 0.0
        self.finished = False
        self.solved_count = 0
        self.skips = 0
        
        # 시간 동결 관리 변수들
        self.time_frozen = False
        self.frozen_start_time = 0.0
        self.total_frozen_time = 0.0
        
        # 녹음 상태 추가
        self.is_recording = False
        self.recording_stream = None
        self.recording_start_time = 0.0
        self._rec_frames = []  # 실시간 녹음 프레임 버퍼

    def start(self):
        """게임 시작"""
        self.reset_session()
        self.start_ts = time.perf_counter()
        self.round = self._next_round()

    def _next_round(self) -> Optional[RoundState]:
        """다음 라운드로 진행"""
        if self.idx >= len(self.items):
            return None
        item = self.items[self.idx]
        self.idx += 1
        return RoundState(target=item["target"], forbidden=item["forbidden"])

    def _time_left(self) -> float:
        """남은 시간 계산"""
        if self.time_mode == "TIME_ATTACK":
            return max(0.0, TIME_ATTACK_SECONDS - self.elapsed)
        return float("inf")

    def _goal_count(self) -> int:
        """목표 횟수 반환"""
        return SPEED_RUN_TARGET_COUNT if self.time_mode == "SPEED_RUN" else 999999

    def freeze_time(self):
        """시간 동결 시작 (음성 인식 및 AI 처리 중)"""
        if not self.time_frozen:
            self.time_frozen = True
            self.frozen_start_time = time.perf_counter()

    def unfreeze_time(self):
        """시간 동결 해제"""
        if self.time_frozen:
            self.time_frozen = False
            freeze_duration = time.perf_counter() - self.frozen_start_time
            self.total_frozen_time += freeze_duration

    def handle_key(self, key):
        """키 입력 처리"""
        if self.finished:
            return
        if key == pygame.K_SPACE:  # SPACE 키로 녹음 시작만
            if not self.is_recording:
                self.start_recording()
        elif key == pygame.K_n:
            self.skip_word()
        elif key == pygame.K_F11:
            pygame.display.toggle_fullscreen()
    
    def handle_key_up(self, key):
        """키를 뗄 때 처리 (SPACE 키를 떼면 녹음 중지)"""
        if key == pygame.K_SPACE and self.is_recording:
            self.stop_recording_and_process()

    def start_recording(self):
        """녹음 시작 - 실시간 스트림으로 즉시 시작"""
        if not self.round or self.is_recording:
            return
        
        try:
            self.is_recording = True
            self._rec_frames = []  # 프레임 버퍼 초기화
            self.recording_start_time = time.perf_counter()
            
            # 실시간 입력 스트림으로 키를 누른 순간부터 녹음
            def audio_callback(indata, frames, time_info, status):
                if status:
                    print(f"오디오 상태: {status}")
                self._rec_frames.append(indata.copy())
            
            self.recording_stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype='float32',
                callback=audio_callback,
                device=None  # 테스트에서 성공한 기본 디바이스
            )
            self.recording_stream.start()
            print("녹음 시작...")
            
        except Exception as e:
            print(f"녹음 시작 실패: {e}")
            self.is_recording = False

    def stop_recording_and_process(self):
        """녹음 중지 및 누적된 프레임 처리"""
        if not self.is_recording or not self.recording_stream:
            return
        
        try:
            # 스트림 중지
            self.recording_stream.stop()
            self.recording_stream.close()
            self.recording_stream = None
            self.is_recording = False
            
            duration = time.perf_counter() - self.recording_start_time
            print(f"녹음 종료 (시간: {duration:.1f}초)")
            
            # 최소 녹음 시간 체크
            if duration < 0.5:
                print("녹음 시간이 너무 짧습니다.")
                return
            
            # 누적된 프레임들을 하나로 합치기
            if not self._rec_frames:
                print("수집된 오디오가 없습니다.")
                return
                
            audio = np.concatenate(self._rec_frames, axis=0).reshape(-1)
            
            # 오디오 품질 확인
            audio_level = float(np.max(np.abs(audio)))
            audio_rms = float(np.sqrt(np.mean(audio**2)))
            print(f"캡처된 오디오 - 최대: {audio_level:.4f}, RMS: {audio_rms:.4f}")
            
            # 음성 처리
            self.process_audio(audio)
            
        except Exception as e:
            print(f"녹음 처리 실패: {e}")
            self.is_recording = False
            if self.recording_stream:
                try:
                    self.recording_stream.stop()
                    self.recording_stream.close()
                except:
                    pass
                self.recording_stream = None

    def process_audio(self, audio: np.ndarray):
        """녹음된 오디오를 처리하여 게임 로직 실행 (파일 저장 없이)"""
        if not self.round:
            return
        
        print("오디오 처리 시작...")
        
        # 시간 동결 시작 (음성 인식 및 AI 처리 중)
        self.freeze_time()
        
        # 1) 오디오를 바이너리 데이터로 변환 (파일 저장 없음)
        try:
            wav_data = audio_array_to_wav_bytes(audio)
            
            # 2) ASR (음성 인식) - 바이너리 데이터 직접 전송
            text = self.client.transcribe_audio_data(wav_data)
            
        except Exception as e:
            print(f"바이너리 방식 실패: {e}, 파일 방식으로 재시도...")
            # Fallback: 파일 저장 방식
            try:
                tmp = f"_tmp_{int(time.time()*1000)}.wav"
                save_wav_from_array(tmp, audio)
                text = self.client.transcribe(tmp)
                try:
                    os.remove(tmp)
                except:
                    pass
            except Exception as e2:
                self.round.feedback = f"음성 처리 완전 실패: {e2}"
                # 시간 동결 해제
                self.unfreeze_time()
                return
        
        print(f"최종 음성 인식 결과: '{text}'")
        
        self.round.last_transcription = text
        if text.startswith("__error__"):
            self.round.feedback = "음성 인식 오류. 다시 시도해주세요."
            # 시간 동결 해제
            self.unfreeze_time()
            return
        
        if not text or text.strip() == "":
            self.round.feedback = "음성이 인식되지 않았습니다. 더 명확하게 말해주세요."
            # 시간 동결 해제
            self.unfreeze_time()
            return

        # 3) 위반 검사 (금지어 + 목표어)
        forbidden_violation, target_violation = check_violations(
            text, self.round.target, self.round.forbidden
        )
        
        if target_violation:
            self.round.target_violation = True
            self.round.feedback = "목표어를 말했습니다! 라운드 실패"
            # 시간 동결 해제
            self.unfreeze_time()
            # 다음 라운드로
            self.round = self._next_round()
            if self.round is None:
                self.finished = True
            return
        
        if forbidden_violation:
            self.round.taboo_violation = forbidden_violation
            self.round.feedback = f"금지어 '{forbidden_violation}' 사용! 라운드 실패"
            # 시간 동결 해제
            self.unfreeze_time()
            # 다음 라운드로
            self.round = self._next_round()
            if self.round is None:
                self.finished = True
            return

        # 4) 설명 누적 → AI 추측 요청
        clean = text.strip()
        if clean:
            self.round.description_history.append(clean)
        
        reply = self.client.ask_guess(self.round.description_history)
        self.round.ai_reply = reply
        guess = extract_guess_token(reply)
        self.round.ai_guess = guess or None

        # 5) 성공 판정 (한글 지원 강화)
        target_original = self.round.target
        target_lower = target_original.lower()
        success = False
        
        # 추측 토큰으로 판정 (대소문자 무시)
        if guess:
            guess_lower = guess.lower()
            if guess_lower == target_lower or guess == target_original:
                success = True
        
        # AI 응답에 목표어가 포함되었는지 확인 (더 정확한 매칭)
        if not success:
            reply_lower = reply.lower()
            # 정확한 단어 매칭 (공백으로 구분된 토큰 기준)
            reply_tokens = reply_lower.split()
            if target_lower in reply_tokens or target_original in reply.split():
                success = True
            # 한글의 경우 서브스트링으로도 확인
            elif target_lower in reply_lower:
                success = True

        # AI 처리 완료 후 시간 동결 해제
        self.unfreeze_time()

        if success:
            self.round.solved = True
            self.score += 1
            self.solved_count += 1
            self.round.feedback = "AI가 정답을 맞혔습니다!"
            
            if self.time_mode == "SPEED_RUN" and self.solved_count >= self._goal_count():
                self.finished = True
            else:
                self.round = self._next_round()
                if self.round is None:
                    self.finished = True
        else:
            self.round.feedback = "더 설명해주세요! (금지어와 목표어는 피해서)"

    def skip_word(self):
        """단어 스킵 (패널티 적용)"""
        self.skips += 1
        if self.time_mode == "TIME_ATTACK" and self.start_ts is not None:
            self.start_ts -= SKIP_PENALTY_SECONDS
        self.round = self._next_round()
        if self.round is None:
            self.finished = True

    def update(self):
        """게임 상태 업데이트"""
        if self.start_ts is not None:
            # 현재 동결 중이면 동결 시간을 추가로 계산
            current_frozen_time = self.total_frozen_time
            if self.time_frozen:
                current_frozen_time += time.perf_counter() - self.frozen_start_time
            
            # 동결된 시간을 제외한 실제 플레이 시간 계산
            self.elapsed = time.perf_counter() - self.start_ts - current_frozen_time
            
            if self.time_mode == "TIME_ATTACK" and self.elapsed >= TIME_ATTACK_SECONDS:
                self.finished = True

    def draw_center_text(self, text: str, font, y: int, color=FG_COLOR):
        """중앙 정렬 텍스트 그리기"""
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(WINDOW_W // 2, y))
        self.screen.blit(surf, rect)

    def wrap_text(self, text: str, font, max_width: int) -> list[str]:
        """텍스트 줄바꿈"""
        words = text.split()
        lines = []
        cur = ""
        for w in words:
            test = (cur + " " + w) if cur else w
            if font.size(test)[0] <= max_width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    def render(self):
        """화면 렌더링 - 네온 오락실 스타일 UI"""
        # 어두운 배경 + 노이즈 효과
        self.screen.fill((10, 5, 15))
        
        # 스캔라인 효과 (오락실 CRT 모니터 느낌)
        for y in range(0, WINDOW_H, 4):
            pygame.draw.line(self.screen, (25, 15, 35), (0, y), (WINDOW_W, y), 1)
        
        # 네온 글로우 효과를 위한 헬퍼 함수
        def draw_neon_text(text, font, x, y, color, glow_color, center=False):
            # 글로우 효과 (여러 레이어)
            for offset in [(4, 4), (3, 3), (2, 2), (1, 1)]:
                glow_surf = font.render(text, True, glow_color)
                if center:
                    glow_rect = glow_surf.get_rect(center=(x, y))
                    self.screen.blit(glow_surf, (glow_rect.x + offset[0], glow_rect.y + offset[1]))
                else:
                    self.screen.blit(glow_surf, (x + offset[0], y + offset[1]))
            
            # 메인 텍스트
            main_surf = font.render(text, True, color)
            if center:
                main_rect = main_surf.get_rect(center=(x, y))
                self.screen.blit(main_surf, main_rect)
            else:
                self.screen.blit(main_surf, (x, y))
        
        def draw_neon_rect(rect, color, glow_color, thickness=3):
            # 글로우 효과
            for i in range(6, 0, -1):
                glow_rect = pygame.Rect(rect.x - i, rect.y - i, rect.width + i*2, rect.height + i*2)
                pygame.draw.rect(self.screen, (*glow_color, 30), glow_rect, thickness + i, border_radius=10)
            
            # 메인 테두리
            pygame.draw.rect(self.screen, color, rect, thickness, border_radius=10)

        # 메인 타이틀 (네온 사인 스타일)
        title_color = (0, 255, 255)  # 시안
        glow_cyan = (0, 100, 100)
        draw_neon_text("VOICE TABOO", self.big, WINDOW_W // 2, 40, title_color, glow_cyan, center=True)
        
        # 부제목
        subtitle_color = (255, 20, 147)  # 핑크
        glow_pink = (100, 10, 60)
        draw_neon_text("ARCADE MODE", self.small, WINDOW_W // 2, 75, subtitle_color, glow_pink, center=True)
        
        # 상태 HUD (오른쪽 상단, 게임기 스타일)
        hud_x = WINDOW_W - 220
        hud_y = 20
        
        # HUD 배경
        hud_bg = pygame.Rect(hud_x - 10, hud_y - 10, 200, 100)
        pygame.draw.rect(self.screen, (5, 5, 20), hud_bg, border_radius=8)
        draw_neon_rect(hud_bg, (50, 255, 150), (20, 100, 60), 2)
        
        # 스코어
        score_color = (50, 255, 150)  # 네온 그린
        draw_neon_text(f"SCORE: {self.score:04d}", self.font, hud_x, hud_y, score_color, (20, 100, 60))
        
        # 시간
        if self.time_mode == "TIME_ATTACK":
            time_left = max(0, int(self._time_left()))
            time_color = (255, 50, 50) if time_left <= 10 else (255, 255, 50)  # 빨강/노랑
            time_glow = (100, 20, 20) if time_left <= 10 else (100, 100, 20)
            time_text = f"TIME: {time_left:02d}"
        else:
            time_color = (255, 255, 50)
            time_glow = (100, 100, 20)
            time_text = f"TIME: {int(self.elapsed):02d}"
            
        draw_neon_text(time_text, self.font, hud_x, hud_y + 30, time_color, time_glow)
        
        # 모드 표시
        mode_text = "TIME ATTACK" if self.time_mode == "TIME_ATTACK" else "SPEED RUN"
        draw_neon_text(mode_text, self.small, hud_x, hud_y + 60, (255, 150, 255), (100, 60, 100))

        # 라운드가 없을 때
        if not self.round:
            self._draw_neon_game_over_screen()
            pygame.display.flip()
            return

        # 게임 종료 시
        if self.finished:
            self._draw_neon_game_complete_screen()
            pygame.display.flip()
            return

        # 메인 게임 영역
        main_y = 120
        
        # 목표어 디스플레이 (네온 사인박스 스타일)
        target_rect = pygame.Rect(80, main_y, WINDOW_W - 160, 90)
        pygame.draw.rect(self.screen, (20, 10, 30), target_rect, border_radius=15)
        draw_neon_rect(target_rect, (0, 255, 255), (0, 100, 100), 4)
        
        # 목표어 라벨
        draw_neon_text("TARGET", self.small, WINDOW_W // 2, main_y + 20, (0, 255, 255), (0, 100, 100), center=True)
        
        # 목표어 메인 텍스트 (더 큰 글로우)
        target_color = (255, 255, 255)
        for offset in [(6, 6), (4, 4), (2, 2)]:
            glow_surf = self.big.render(self.round.target, True, (0, 150, 150))
            glow_rect = glow_surf.get_rect(center=(WINDOW_W // 2, main_y + 55))
            self.screen.blit(glow_surf, (glow_rect.x + offset[0], glow_rect.y + offset[1]))
        
        target_surf = self.big.render(self.round.target, True, target_color)
        target_rect_center = target_surf.get_rect(center=(WINDOW_W // 2, main_y + 55))
        self.screen.blit(target_surf, target_rect_center)
        
        # 금지어 영역 (경고 사인 스타일)
        forbidden_y = main_y + 110
        forbidden_rect = pygame.Rect(80, forbidden_y, WINDOW_W - 160, 80)
        pygame.draw.rect(self.screen, (30, 10, 10), forbidden_rect, border_radius=15)
        draw_neon_rect(forbidden_rect, (255, 50, 50), (100, 20, 20), 4)
        
        # 금지어 라벨 (깜빡이는 효과)
        warning_alpha = int(127 + 127 * math.sin(time.perf_counter() * 3))
        warning_color = (255, warning_alpha, warning_alpha)
        draw_neon_text("FORBIDDEN", self.small, WINDOW_W // 2, forbidden_y + 15, warning_color, (100, 20, 20), center=True)
        
        # 금지어 목록
        forbidden_text = " • ".join(self.round.forbidden)
        lines = self.wrap_text(forbidden_text, self.small, WINDOW_W - 200)
        for i, line in enumerate(lines):
            draw_neon_text(line, self.small, WINDOW_W // 2, forbidden_y + 40 + i * 20, (255, 100, 100), (100, 40, 40), center=True)

        # 컨트롤 영역 (더 넓은 간격)
        control_y = forbidden_y + 120
        
        if self.is_recording:
            # 녹음 중 - 펄싱 효과 (더 큰 영역)
            recording_time = time.perf_counter() - self.recording_start_time
            pulse = int(127 + 127 * math.sin(recording_time * 8))
            
            # 펄싱 배경 (더 큰 크기)
            rec_bg = pygame.Rect(WINDOW_W // 2 - 200, control_y - 20, 400, 80)
            pygame.draw.rect(self.screen, (pulse // 4, 0, 0), rec_bg, border_radius=15)
            draw_neon_rect(rec_bg, (255, pulse, pulse), (100, pulse // 2, pulse // 2), 4)
            
            # 녹음 텍스트 (더 큰 폰트)
            rec_text = f"◉ REC {recording_time:.1f}s"
            draw_neon_text(rec_text, self.big, WINDOW_W // 2, control_y + 5, (255, pulse, pulse), (100, pulse // 3, pulse // 3), center=True)
            
            # 마이크 아이콘 (더 큰 애니메이션)
            mic_center_x = WINDOW_W // 2 - 120
            for i in range(4):
                radius = 12 + i * 6 + int(6 * math.sin(recording_time * 8 + i))
                color_intensity = 255 - i * 40
                pygame.draw.circle(self.screen, (color_intensity, 0, 0), (mic_center_x, control_y + 20), radius, 3)
            
            # 웨이브 효과 (오른쪽)
            wave_x = WINDOW_W // 2 + 120
            for i in range(3):
                wave_offset = int(20 * math.sin(recording_time * 6 + i * 2))
                wave_y = control_y + 20 + wave_offset
                pygame.draw.circle(self.screen, (255, pulse // 2, pulse // 2), (wave_x + i * 25, wave_y), 4)
            
            draw_neon_text("Release SPACE to stop recording", self.small, WINDOW_W // 2, control_y + 50, (255, 200, 200), (100, 80, 80), center=True)
        else:
            # 간단한 상태 표시만 (키 설명 제거)
            status_bg = pygame.Rect(WINDOW_W // 2 - 150, control_y, 300, 60)
            pygame.draw.rect(self.screen, (0, 20, 30), status_bg, border_radius=12)
            draw_neon_rect(status_bg, (0, 200, 255), (0, 80, 100), 3)
            
            # 상태 메시지
            draw_neon_text("READY TO RECORD", self.font, WINDOW_W // 2, control_y + 15, (0, 255, 255), (0, 100, 100), center=True)
            draw_neon_text("Press SPACE to speak", self.small, WINDOW_W // 2, control_y + 40, (150, 200, 255), (60, 80, 100), center=True)

        # 채팅 영역 (더 넓은 간격)
        chat_y = control_y + 120
        
        if hasattr(self.round, 'last_transcription') and self.round.last_transcription:
            # 사용자 메시지 (터미널 입력 스타일, 더 넓은 간격)
            user_bg = pygame.Rect(60, chat_y, WINDOW_W - 120, 70)
            pygame.draw.rect(self.screen, (0, 20, 0), user_bg, border_radius=12)
            draw_neon_rect(user_bg, (0, 255, 0), (0, 100, 0), 3)
            
            user_prefix = "► YOU:"
            draw_neon_text(user_prefix, self.font, 80, chat_y + 15, (0, 255, 0), (0, 100, 0))
            
            # 텍스트 (더 큰 여백)
            user_text_lines = self.wrap_text(self.round.last_transcription, self.small, WINDOW_W - 240)
            for i, line in enumerate(user_text_lines):
                draw_neon_text(line, self.small, 80, chat_y + 40 + i * 22, (200, 255, 200), (80, 100, 80))
            
            chat_y += 90
        
        if hasattr(self.round, 'ai_reply') and self.round.ai_reply:
            # AI 응답 (홀로그램 스타일, 더 넓은 간격)
            ai_bg = pygame.Rect(60, chat_y, WINDOW_W - 120, 70)
            ai_color = (100, 200, 255) if not self.round.solved else (255, 200, 100)
            ai_glow = (40, 80, 100) if not self.round.solved else (100, 80, 40)
            
            pygame.draw.rect(self.screen, (*ai_glow, 50), ai_bg, border_radius=12)
            draw_neon_rect(ai_bg, ai_color, ai_glow, 3)
            
            ai_prefix = "◄ AI:"
            draw_neon_text(ai_prefix, self.font, 80, chat_y + 15, ai_color, ai_glow)
            
            ai_text_lines = self.wrap_text(self.round.ai_reply, self.small, WINDOW_W - 240)
            for i, line in enumerate(ai_text_lines):
                draw_neon_text(line, self.small, 80, chat_y + 40 + i * 22, ai_color, ai_glow)
            
            chat_y += 90
        
        # 피드백 메시지 (상태 표시등 스타일, 더 넓은 간격)
        if hasattr(self.round, 'feedback') and self.round.feedback:
            feedback_y = chat_y + 30
            
            if "정답" in self.round.feedback or "맞혔" in self.round.feedback:
                feedback_color = (0, 255, 0)
                feedback_glow = (0, 100, 0)
                icon = "✓ SUCCESS"
            elif "금지어" in self.round.feedback or "목표어" in self.round.feedback:
                feedback_color = (255, 0, 0)
                feedback_glow = (100, 0, 0)
                icon = "✗ VIOLATION"
            else:
                feedback_color = (255, 255, 0)
                feedback_glow = (100, 100, 0)
                icon = "→ CONTINUE"
            
            # 상태 표시등 (더 큰 크기)
            indicator_rect = pygame.Rect(WINDOW_W // 2 - 150, feedback_y, 300, 40)
            pygame.draw.rect(self.screen, (10, 10, 10), indicator_rect, border_radius=8)
            draw_neon_rect(indicator_rect, feedback_color, feedback_glow, 3)
            
            status_text = f"{icon}"
            draw_neon_text(status_text, self.font, WINDOW_W // 2, feedback_y + 8, feedback_color, feedback_glow, center=True)
            
            # 피드백 텍스트 (아래줄)
            draw_neon_text(self.round.feedback, self.small, WINDOW_W // 2, feedback_y + 25, feedback_color, feedback_glow, center=True)

        pygame.display.flip()
    
    def _draw_neon_game_over_screen(self):
        """네온 스타일 게임 오버 화면"""
        # 어두운 오버레이
        overlay = pygame.Surface((WINDOW_W, WINDOW_H))
        overlay.set_alpha(180)
        overlay.fill((5, 0, 10))
        self.screen.blit(overlay, (0, 0))
        
        # 게임 오버 텍스트 (깜빡이는 네온)
        blink = int(time.perf_counter() * 3) % 2
        if blink:
            self._draw_neon_text_centered("GAME OVER", self.big, WINDOW_H // 2 - 60, (255, 0, 0), (100, 0, 0))
        
        self._draw_neon_text_centered(f"FINAL SCORE: {self.score:04d}", self.font, WINDOW_H // 2, (0, 255, 255), (0, 100, 100))
        self._draw_neon_text_centered("Press ESC to exit", self.small, WINDOW_H // 2 + 40, (255, 255, 0), (100, 100, 0))
    
    def _draw_neon_game_complete_screen(self):
        """네온 스타일 게임 완료 화면"""
        # 승리 오버레이
        overlay = pygame.Surface((WINDOW_W, WINDOW_H))
        overlay.set_alpha(180)
        overlay.fill((0, 10, 0))
        self.screen.blit(overlay, (0, 0))
        
        # 승리 텍스트 (레인보우 효과)
        rainbow_offset = int(time.perf_counter() * 2) % 6
        colors = [(255, 0, 0), (255, 150, 0), (255, 255, 0), (0, 255, 0), (0, 150, 255), (150, 0, 255)]
        win_color = colors[rainbow_offset]
        
        self._draw_neon_text_centered("VICTORY!", self.big, WINDOW_H // 2 - 60, win_color, tuple(c // 3 for c in win_color))
        
        if self.time_mode == "SPEED_RUN":
            time_text = f"TIME: {int(self.elapsed):02d}s"
        else:
            time_text = "MISSION COMPLETE"
            
        self._draw_neon_text_centered(time_text, self.font, WINDOW_H // 2 - 10, (0, 255, 255), (0, 100, 100))
        self._draw_neon_text_centered(f"SCORE: {self.score:04d}", self.font, WINDOW_H // 2 + 20, (0, 255, 0), (0, 100, 0))
        self._draw_neon_text_centered("Press ESC to exit", self.small, WINDOW_H // 2 + 60, (255, 255, 0), (100, 100, 0))
    
    def _draw_neon_text_centered(self, text, font, y, color, glow_color):
        """네온 텍스트 중앙 정렬 헬퍼"""
        # 글로우 효과
        for offset in [(4, 4), (3, 3), (2, 2), (1, 1)]:
            glow_surf = font.render(text, True, glow_color)
            glow_rect = glow_surf.get_rect(center=(WINDOW_W // 2 + offset[0], y + offset[1]))
            self.screen.blit(glow_surf, glow_rect)
        
        # 메인 텍스트
        main_surf = font.render(text, True, color)
        main_rect = main_surf.get_rect(center=(WINDOW_W // 2, y))
        self.screen.blit(main_surf, main_rect)
