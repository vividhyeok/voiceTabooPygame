"""
메인 메뉴 시스템
"""
import json
import math
import random
import time
import pygame
from config import WINDOW_W, WINDOW_H


class MainMenu:
    """게임 메인 메뉴 클래스"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self._init_fonts()
        self.selected_index = 0
        self.menu_items = ["START GAME", "SWAP MODE", "HELP"]
        self.current_mode = "TIME_ATTACK"
        self.scores = self.load_scores()
        
        # 이름 입력 관련
        self.player_name = ""
        self.name_input_active = False
        self.name_cursor_blink = 0
        
    def _init_fonts(self):
        """폰트 초기화"""
        try:
            self.title_font = pygame.font.SysFont("malgun gothic", 48, bold=True)
            self.big_font = pygame.font.SysFont("malgun gothic", 32, bold=True)
            self.font = pygame.font.SysFont("malgun gothic", 24)
            self.small_font = pygame.font.SysFont("malgun gothic", 18)
        except:
            try:
                self.title_font = pygame.font.SysFont("gulim", 48, bold=True)
                self.big_font = pygame.font.SysFont("gulim", 32, bold=True)
                self.font = pygame.font.SysFont("gulim", 24)
                self.small_font = pygame.font.SysFont("gulim", 18)
            except:
                self.title_font = pygame.font.SysFont(None, 48)
                self.big_font = pygame.font.SysFont(None, 32)
                self.font = pygame.font.SysFont(None, 24)
                self.small_font = pygame.font.SysFont(None, 18)
    
    def load_scores(self):
        """점수 데이터 로드 (모드별 파일)"""
        try:
            filename = f"scores_{self.current_mode.lower()}.json"
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            # 기본 점수 데이터 (모든 점수 0)
            return [
                {"name": "MASTER", "score": 0, "mode": self.current_mode, "time": 0},
                {"name": "EXPERT", "score": 0, "mode": self.current_mode, "time": 0},
                {"name": "PLAYER", "score": 0, "mode": self.current_mode, "time": 0},
                {"name": "ROOKIE", "score": 0, "mode": self.current_mode, "time": 0},
                {"name": "NEWBIE", "score": 0, "mode": self.current_mode, "time": 0}
            ]
    
    def save_scores(self):
        """점수 데이터 저장 (모드별 파일)"""
        try:
            filename = f"scores_{self.current_mode.lower()}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.scores, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"점수 저장 실패: {e}")
    
    def reload_scores_for_mode(self):
        """모드 변경 시 해당 모드의 점수 다시 로드"""
        self.scores = self.load_scores()
    
    def add_score(self, name, score, mode, elapsed_time):
        """새 점수 추가"""
        # 0점도 저장 가능
        new_score = {
            "name": name,
            "score": score,
            "mode": mode,
            "time": int(elapsed_time)
        }
        
        self.scores.append(new_score)
        # 점수순으로 정렬 (높은 점수부터)
        self.scores.sort(key=lambda x: x["score"], reverse=True)
        # 상위 10개만 유지
        self.scores = self.scores[:10]
        self.save_scores()
    
    def handle_key(self, key):
        """키 입력 처리"""
        if self.name_input_active:
            return self.handle_name_input(key)
        
        if key == pygame.K_UP:
            self.selected_index = (self.selected_index - 1) % len(self.menu_items)
        elif key == pygame.K_DOWN:
            self.selected_index = (self.selected_index + 1) % len(self.menu_items)
        elif key == pygame.K_RETURN:
            return self.handle_selection()
        return None
    
    def handle_name_input(self, key):
        """이름 입력 처리"""
        if key == pygame.K_RETURN:
            if len(self.player_name.strip()) >= 1:
                self.name_input_active = False
                return "START_GAME_WITH_NAME"
        elif key == pygame.K_ESCAPE:
            self.name_input_active = False
            self.player_name = ""
        elif key == pygame.K_BACKSPACE:
            self.player_name = self.player_name[:-1]
        else:
            # 문자 입력 처리
            char = self.get_char_from_key(key)
            if char and len(self.player_name) < 10:  # 최대 10글자
                self.player_name += char
        return None
    
    def get_char_from_key(self, key):
        """키에서 문자 추출"""
        # 영문자
        if pygame.K_a <= key <= pygame.K_z:
            return chr(key - pygame.K_a + ord('A'))
        # 숫자
        elif pygame.K_0 <= key <= pygame.K_9:
            return chr(key - pygame.K_0 + ord('0'))
        # 스페이스
        elif key == pygame.K_SPACE:
            return ' '
        return None
    
    def handle_selection(self):
        """선택된 메뉴 처리"""
        selected = self.menu_items[self.selected_index]
        
        if selected == "START GAME":
            # 이름 입력 화면으로 전환
            self.name_input_active = True
            self.player_name = ""
            return None
        elif selected == "SWAP MODE":
            self.current_mode = "SPEED_RUN" if self.current_mode == "TIME_ATTACK" else "TIME_ATTACK"
            # 모드 변경 시 해당 모드의 점수 로드
            self.reload_scores_for_mode()
            return None
        elif selected == "HELP":
            return "SHOW_HELP"
        
        return None
    
    def draw_neon_text(self, text, font, x, y, color, glow_color, center=False):
        """네온 텍스트 그리기"""
        # 글로우 효과
        for offset in [(3, 3), (2, 2), (1, 1)]:
            glow_surf = font.render(text, True, glow_color)
            if center:
                glow_rect = glow_surf.get_rect(center=(x + offset[0], y + offset[1]))
                self.screen.blit(glow_surf, glow_rect)
            else:
                self.screen.blit(glow_surf, (x + offset[0], y + offset[1]))
        
        # 메인 텍스트
        main_surf = font.render(text, True, color)
        if center:
            main_rect = main_surf.get_rect(center=(x, y))
            self.screen.blit(main_surf, main_rect)
        else:
            self.screen.blit(main_surf, (x, y))
    
    def draw_neon_rect(self, rect, color, glow_color, thickness=3):
        """네온 사각형 그리기"""
        # 글로우 효과
        for i in range(5, 0, -1):
            glow_rect = pygame.Rect(rect.x - i, rect.y - i, rect.width + i*2, rect.height + i*2)
            pygame.draw.rect(self.screen, (*glow_color, 40), glow_rect, thickness + i, border_radius=10)
        
        # 메인 테두리
        pygame.draw.rect(self.screen, color, rect, thickness, border_radius=10)
    
    def render(self):
        """메인 메뉴 렌더링"""
        # 어두운 배경 + 8bit 스타일 스캔라인
        self.screen.fill((5, 2, 10))
        
        # 8bit 스타일 스캔라인 효과 (더 굵고 색상 변화)
        scanline_time = pygame.time.get_ticks() * 0.01
        for y in range(0, WINDOW_H, 6):
            intensity = int(20 + 10 * math.sin(scanline_time + y * 0.1))
            color = (intensity // 3, intensity // 4, intensity)
            pygame.draw.line(self.screen, color, (0, y), (WINDOW_W, y), 2)
            
        # 8bit 스타일 노이즈 효과
        for _ in range(30):
            x = random.randint(0, WINDOW_W)
            y = random.randint(0, WINDOW_H)
            size = random.randint(1, 2)
            intensity = random.randint(8, 25)
            pygame.draw.rect(self.screen, (intensity, intensity, intensity), (x, y, size, size))
        
        if self.name_input_active:
            self.draw_name_input_screen()
        else:
            self.draw_main_menu_screen()
        
        pygame.display.flip()
    
    def draw_name_input_screen(self):
        """이름 입력 화면 그리기"""
        # 메인 타이틀
        title_color = (0, 255, 255)
        self.draw_neon_text("ENTER YOUR NAME", self.title_font, WINDOW_W // 2, 150, 
                           title_color, (0, 100, 100), center=True)
        
        # 이름 입력 박스
        input_rect = pygame.Rect(WINDOW_W // 2 - 200, 250, 400, 80)
        pygame.draw.rect(self.screen, (10, 5, 20), input_rect, border_radius=15)
        self.draw_neon_rect(input_rect, (255, 255, 100), (100, 100, 40), 4)
        
        # 입력된 이름 표시 (위치 조정)
        display_name = self.player_name
        
        # 커서 깜빡임 효과
        self.name_cursor_blink += 1
        if self.name_cursor_blink % 60 < 30:  # 30프레임마다 깜빡임
            display_name += "|"
        
        name_color = (255, 255, 255)
        self.draw_neon_text(display_name, self.big_font, WINDOW_W // 2, 295, 
                           name_color, (100, 100, 100), center=True)
        
        # 안내 텍스트
        guide_color = (200, 200, 255)
        self.draw_neon_text("Use A-Z, 0-9, SPACE (Max 10 chars)", self.font, WINDOW_W // 2, 380, 
                           guide_color, (80, 80, 100), center=True)
        
        self.draw_neon_text("ENTER to confirm • ESC to cancel", self.font, WINDOW_W // 2, 420, 
                           guide_color, (80, 80, 100), center=True)
        
        # 현재 모드 표시
        mode_color = (255, 150, 255)
        mode_text = f"Mode: {self.current_mode.replace('_', ' ')}"
        self.draw_neon_text(mode_text, self.font, WINDOW_W // 2, 480, 
                           mode_color, (100, 60, 100), center=True)
    
    def draw_main_menu_screen(self):
        """메인 메뉴 화면 그리기"""
        
        # 메인 타이틀 (8bit 레트로 스타일)
        title_time = time.perf_counter()
        title_colors = [(255, 0, 100), (100, 255, 255), (255, 255, 100)]
        title_color = title_colors[int(title_time) % len(title_colors)]
        
        # 8bit 스타일 그림자 효과
        for offset in range(4, 0, -1):
            shade_intensity = offset * 15
            shade_color = (shade_intensity, shade_intensity, shade_intensity)
            self.draw_neon_text("VOICE TABOO", self.title_font, WINDOW_W // 2 + offset, 80 + offset, 
                               shade_color, shade_color, center=True)
        
        self.draw_neon_text("VOICE TABOO", self.title_font, WINDOW_W // 2, 80, 
                           title_color, tuple(c // 3 for c in title_color), center=True)
        
        # 8bit 스타일 장식 픽셀들
        pixel_time = pygame.time.get_ticks() * 0.005
        for i in range(15):
            x = WINDOW_W // 2 - 150 + i * 20
            y = 50 + int(3 * math.sin(pixel_time + i * 0.5))
            color = [(255, 0, 100), (0, 255, 255), (255, 255, 0)][i % 3]
            pygame.draw.rect(self.screen, color, (x, y, 4, 4))
            pygame.draw.rect(self.screen, color, (x, y + 70, 4, 4))
        
        subtitle_color = (150, 150, 255)
        self.draw_neon_text("ARCADE EDITION", self.font, WINDOW_W // 2, 120, 
                           subtitle_color, (60, 60, 100), center=True)
        
        # 좌측 순위표
        self.draw_leaderboard()
        
        # 우측 메뉴
        self.draw_menu()
        
        # 하단 모드 표시
        self.draw_mode_info()
    
    def draw_leaderboard(self):
        """순위표 그리기 (좌측, 균형 잡힌 위치)"""
        # 좌측 여백을 늘려서 중앙 정렬
        left_margin = 60
        board_width = 320
        
        # 순위표 배경
        board_rect = pygame.Rect(left_margin, 180, board_width, 400)
        pygame.draw.rect(self.screen, (10, 5, 15), board_rect, border_radius=15)
        self.draw_neon_rect(board_rect, (0, 255, 150), (0, 100, 60), 4)
        
        # 순위표 제목
        title_x = left_margin + board_width // 2
        self.draw_neon_text("★ LEADERBOARD ★", self.big_font, title_x, 210, 
                           (0, 255, 150), (0, 100, 60), center=True)
        
        # 현재 모드 표시
        mode_display = self.current_mode.replace("_", " ")
        self.draw_neon_text(f"({mode_display})", self.small_font, title_x, 235, 
                           (150, 255, 150), (60, 100, 60), center=True)
        
        # 헤더
        header_y = 260
        self.draw_neon_text("RANK", self.font, left_margin + 20, header_y, (255, 255, 0), (100, 100, 0))
        self.draw_neon_text("NAME", self.font, left_margin + 80, header_y, (255, 255, 0), (100, 100, 0))
        self.draw_neon_text("SCORE", self.font, left_margin + 180, header_y, (255, 255, 0), (100, 100, 0))
        self.draw_neon_text("TIME", self.font, left_margin + 250, header_y, (255, 255, 0), (100, 100, 0))
        
        # 순위 목록
        for i, score_data in enumerate(self.scores[:8]):  # 상위 8개만 표시
            y = header_y + 35 + i * 35
            
            # 순위별 색상
            if i == 0:
                rank_color = (255, 215, 0)  # 금색
                glow_color = (100, 86, 0)
            elif i == 1:
                rank_color = (192, 192, 192)  # 은색
                glow_color = (76, 76, 76)
            elif i == 2:
                rank_color = (205, 127, 50)  # 동색
                glow_color = (82, 51, 20)
            else:
                rank_color = (200, 200, 255)  # 기본
                glow_color = (80, 80, 100)
            
            # 순위
            self.draw_neon_text(f"{i+1:2d}", self.font, left_margin + 20, y, rank_color, glow_color)
            
            # 이름 (최대 6글자)
            name = score_data["name"][:6]
            self.draw_neon_text(name, self.font, left_margin + 80, y, rank_color, glow_color)
            
            # 점수
            self.draw_neon_text(f"{score_data['score']:3d}", self.font, left_margin + 180, y, rank_color, glow_color)
            
            # 시간
            time_text = f"{score_data['time']:3d}s" if score_data['time'] > 0 else "---"
            self.draw_neon_text(time_text, self.small_font, left_margin + 250, y, rank_color, glow_color)
    
    def draw_menu(self):
        """메뉴 그리기 (우측, 균형 잡힌 위치)"""
        # 우측 여백을 맞춰서 중앙 정렬
        right_margin = 60
        menu_width = 320
        menu_x = WINDOW_W - right_margin - menu_width
        
        # 메뉴 배경
        menu_rect = pygame.Rect(menu_x, 180, menu_width, 280)
        pygame.draw.rect(self.screen, (5, 10, 20), menu_rect, border_radius=15)
        self.draw_neon_rect(menu_rect, (100, 150, 255), (40, 60, 100), 4)
        
        # 메뉴 제목
        title_x = menu_x + menu_width // 2
        self.draw_neon_text("▶ MAIN MENU ◀", self.big_font, title_x, 210, 
                           (100, 150, 255), (40, 60, 100), center=True)
        
        # 메뉴 항목들
        menu_start_y = 280
        for i, item in enumerate(self.menu_items):
            y = menu_start_y + i * 60
            
            # 선택된 항목 강조
            if i == self.selected_index:
                # 선택 표시 배경 (테두리를 더 아래로)
                select_rect = pygame.Rect(menu_x + 20, y - 5, menu_width - 40, 50)
                pulse = int(127 + 127 * math.sin(time.perf_counter() * 4))
                
                # 8bit 스타일 배경
                pygame.draw.rect(self.screen, (pulse // 4, pulse // 6, pulse // 3), select_rect, border_radius=8)
                self.draw_neon_rect(select_rect, (255, pulse, 100), (100, pulse // 2, 40), 3)
                
                # 8bit 스타일 픽셀 테두리 효과
                pixel_size = 4
                for j in range(0, select_rect.width, pixel_size * 3):
                    pygame.draw.rect(self.screen, (255, 255, 0), 
                                   (select_rect.x + j, select_rect.y - 3, pixel_size, 3))
                    pygame.draw.rect(self.screen, (255, 255, 0), 
                                   (select_rect.x + j, select_rect.bottom, pixel_size, 3))
                
                # 8bit 스타일 사각형 인디케이터 (네모를 더 많이 아래로)
                indicator_x = menu_x + 35
                indicator_y = y + 18
                
                # 8bit 스타일 펄스 효과
                bit_pulse = int(8 + 6 * abs(math.sin(pygame.time.get_ticks() * 0.01)))
                
                # 레트로 사각형 인디케이터
                pygame.draw.rect(self.screen, (255, 255, 100), 
                               (indicator_x - bit_pulse//2, indicator_y - bit_pulse//2, bit_pulse, bit_pulse))
                pygame.draw.rect(self.screen, (255, 255, 200), 
                               (indicator_x - bit_pulse//3, indicator_y - bit_pulse//3, bit_pulse//1.5, bit_pulse//1.5))
                pygame.draw.rect(self.screen, (255, 255, 255), 
                               (indicator_x - 2, indicator_y - 2, 4, 4))
                
                # 선택된 항목 텍스트
                text_color = (255, 255, 255)
                text_glow = (100, 100, 100)
            else:
                # 일반 항목 텍스트
                text_color = (150, 200, 255)
                text_glow = (60, 80, 100)
            
            self.draw_neon_text(item, self.font, menu_x + 70, y + 5, text_color, text_glow)
    
    def draw_mode_info(self):
        """모드 정보 표시 (우측 하단, 균형 잡힌 위치)"""
        # 우측 여백에 맞춰서 위치 조정
        right_margin = 60
        info_width = 320
        info_x = WINDOW_W - right_margin - info_width
        
        # 모드 정보 배경
        mode_rect = pygame.Rect(info_x, 480, info_width, 100)
        pygame.draw.rect(self.screen, (15, 8, 5), mode_rect, border_radius=12)
        
        if self.current_mode == "TIME_ATTACK":
            mode_color = (255, 100, 100)
            mode_glow = (100, 40, 40)
            mode_text = "TIME ATTACK"
            desc_text = "2분 안에 최대한 많은 단어!"
        else:
            mode_color = (100, 255, 100)
            mode_glow = (40, 100, 40)
            mode_text = "SPEED RUN"
            desc_text = "10개 단어를 최대한 빠르게!"
        
        self.draw_neon_rect(mode_rect, mode_color, mode_glow, 3)
        
        # 모드 이름
        mode_title_x = info_x + info_width // 2
        self.draw_neon_text(f"MODE: {mode_text}", self.font, mode_title_x, 500, 
                           mode_color, mode_glow, center=True)
        
        # 모드 설명
        self.draw_neon_text(desc_text, self.small_font, mode_title_x, 530, 
                           mode_color, mode_glow, center=True)
        
        # 조작법 안내
        control_color = (200, 200, 200)
        control_glow = (80, 80, 80)
        self.draw_neon_text("↑↓ 선택   ENTER 실행", self.small_font, mode_title_x, 555, 
                           control_color, control_glow, center=True)
