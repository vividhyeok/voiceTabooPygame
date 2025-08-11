"""
Voice Taboo – Pygame only (OpenAI Whisper + LLM)

개선된 버전:
- 목표어 말하기 금지 추가
- 코드를 여러 파일로 분리
- 더 나은 에러 처리
- 네온 아케이드 스타일 UI
- 메인 메뉴 시스템 추가

Rule:
  플레이어는 화면에 보이는 "목표어"와 "금지어"를 참고해,
  금지어와 목표어를 말하지 않고 목표어를 설명한다. AI(모델)는 설명만 듣고
  목표어를 직접 말해야 하며, 맞히면 점수 획득.

Setup:
  pip install pygame sounddevice numpy openai
  set OPENAI_API_KEY=your_key_here
  
  # Optional
  set TABOO_JSON=taboo_bank.json  # JSON path
  set ROUNDS=12                   # rounds per session
"""
import time
import pygame
import subprocess
import sys
import os

from config import WINDOW_W, WINDOW_H, BG_COLOR, FG_COLOR, ACCENT, MUTED, FONT_NAME, ROUNDS_PER_SESSION, TABOO_JSON_PATH
from game import Game
from main_menu import MainMenu


def show_help():
    """key.txt 파일을 기본 텍스트 에디터로 열기"""
    try:
        if os.path.exists("key.txt"):
            if sys.platform == "win32":
                os.startfile("key.txt")
            elif sys.platform == "darwin":  # macOS
                subprocess.call(["open", "key.txt"])
            else:  # Linux
                subprocess.call(["xdg-open", "key.txt"])
        else:
            print("key.txt 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"도움말 파일 열기 실패: {e}")


def main():
    """메인 실행 함수"""
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Voice Taboo – Arcade Edition")

    clock = pygame.time.Clock()
    
    # 메인 메뉴 초기화
    main_menu = MainMenu(screen)
    game = None
    current_state = "MAIN_MENU"  # MAIN_MENU, PLAYING, GAME_OVER
    
    # 게임 종료 후 결과 저장용
    final_score = 0
    final_mode = ""
    final_time = 0
    
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if current_state == "MAIN_MENU":
                    # 메인 메뉴에서의 키 처리
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    else:
                        menu_action = main_menu.handle_key(event.key)
                        
                        if menu_action == "START_GAME_WITH_NAME":
                            # 이름과 함께 게임 시작
                            game = Game(screen)
                            game.time_mode = main_menu.current_mode
                            game.player_name = main_menu.player_name.strip() or "PLAYER"
                            game.start()
                            current_state = "PLAYING"
                            
                        elif menu_action == "SHOW_HELP":
                            show_help()
                
                elif current_state == "PLAYING":
                    # 게임 중 키 처리
                    if event.key == pygame.K_ESCAPE:
                        current_state = "MAIN_MENU"
                        game = None
                    else:
                        game.handle_key(event.key)
                
                elif current_state == "GAME_OVER":
                    # 게임 오버에서 메인 메뉴로
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                        current_state = "MAIN_MENU"
                        game = None
            
            elif event.type == pygame.KEYUP:
                if current_state == "PLAYING" and game:
                    game.handle_key_up(event.key)
        
        # 게임 상태 업데이트 및 렌더링
        if current_state == "MAIN_MENU":
            main_menu.render()
            
        elif current_state == "PLAYING":
            if game:
                game.update()
                
                # 게임 종료 체크
                if game.finished or not game.round:
                    # 모든 게임 결과를 저장 (0점 포함)
                    main_menu.add_score(game.player_name, game.score, game.time_mode, game.elapsed)
                    current_state = "GAME_OVER"
                    final_score = game.score
                    final_mode = game.time_mode
                    final_time = game.elapsed
                else:
                    game.render()
            
        elif current_state == "GAME_OVER":
            # 게임 오버 화면 렌더링
            screen.fill((5, 0, 10))
            
            # 스캔라인 효과
            for y in range(0, WINDOW_H, 4):
                pygame.draw.line(screen, (15, 8, 20), (0, y), (WINDOW_W, y), 1)
            
            # 게임 오버 텍스트
            try:
                big_font = pygame.font.SysFont("malgun gothic", 48, bold=True)
                font = pygame.font.SysFont("malgun gothic", 32)
                small_font = pygame.font.SysFont("malgun gothic", 24)
            except:
                big_font = pygame.font.SysFont(None, 48)
                font = pygame.font.SysFont(None, 32)
                small_font = pygame.font.SysFont(None, 24)
            
            # 결과 화면
            title_surf = big_font.render("GAME COMPLETE!", True, (0, 255, 255))
            title_rect = title_surf.get_rect(center=(WINDOW_W // 2, WINDOW_H // 2 - 100))
            screen.blit(title_surf, title_rect)
            
            score_surf = font.render(f"Final Score: {final_score}", True, (0, 255, 0))
            score_rect = score_surf.get_rect(center=(WINDOW_W // 2, WINDOW_H // 2 - 50))
            screen.blit(score_surf, score_rect)
            
            mode_surf = font.render(f"Mode: {final_mode}", True, (255, 255, 0))
            mode_rect = mode_surf.get_rect(center=(WINDOW_W // 2, WINDOW_H // 2))
            screen.blit(mode_surf, mode_rect)
            
            time_surf = font.render(f"Time: {int(final_time)}s", True, (255, 150, 0))
            time_rect = time_surf.get_rect(center=(WINDOW_W // 2, WINDOW_H // 2 + 50))
            screen.blit(time_surf, time_rect)
            
            continue_surf = small_font.render("Press ESC or ENTER to continue", True, (200, 200, 200))
            continue_rect = continue_surf.get_rect(center=(WINDOW_W // 2, WINDOW_H // 2 + 120))
            screen.blit(continue_surf, continue_rect)
            
            pygame.display.flip()
        
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
