import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import random
from PIL import Image
import io
import os
from urllib.request import urlopen
import json
import pygame

# Import các module mới
from database import DatabaseManager
from audio_manager import AudioManager
from ai_opponent import AIOpponent

# =================== 🎀 Hello Kitty Color Palette VIP 🎀 ===================
KITTY_BG = "#FFF0F5"
KITTY_BG_ALT = "#FFFCF0"
KITTY_MAIN_PINK = "#F783AC"
KITTY_ACCENT_PINK = "#FFC0CB"
KITTY_PURPLE_HOVER = "#DD90C0"
KITTY_TEXT = "#555555"
KITTY_ERROR_RED = "#FF6666"

# =================== Sudoku Logic ===================
def is_valid(board, row, col, num):
    if num in board[row]:
        return False
    for r in range(9):
        if board[r][col] == num:
            return False
    start_row, start_col = 3 * (row // 3), 3 * (col // 3)
    for r in range(start_row, start_row + 3):
        for c in range(start_col, start_col + 3):
            if board[r][c] == num:
                return False
    return True

def solve_board(board):
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                for num in range(1, 10):
                    if is_valid(board, row, col, num):
                        board[row][col] = num
                        if solve_board(board):
                            return True
                        board[row][col] = 0
                return False
    return True

def generate_board(difficulty_level):
    difficulty_settings = {
        "Easy": 35,
        "Medium": 45,  
        "Hard": 50,
        "Expert": 55
    }
    
    cells_to_remove = difficulty_settings.get(difficulty_level, 45)
    
    board = [[0 for _ in range(9)] for _ in range(9)]
    for i in range(3):
        for j in range(3):
            row = i * 3 + random.randint(0, 2)
            col = j * 3 + random.randint(0, 2)
            num = random.randint(1, 9)
            while not is_valid(board, row, col, num):
                num = random.randint(1, 9)
            board[row][col] = num
    if not solve_board(board):
        return generate_board(difficulty_level)
    solved_board = [row[:] for row in board]
    
    removed = 0
    max_attempts = 150
    attempts = 0
    
    while removed < cells_to_remove and attempts < max_attempts:
        row, col = random.randint(0, 8), random.randint(0, 8)
        if board[row][col] != 0:
            temp = board[row][col]
            board[row][col] = 0
            
            temp_board = [row[:] for row in board]
            solution_count = count_solutions(temp_board)
            
            if solution_count == 1:
                removed += 1
            else:
                board[row][col] = temp
                
            attempts += 1
    
    if removed < cells_to_remove:
        while removed < cells_to_remove:
            row, col = random.randint(0, 8), random.randint(0, 8)
            if board[row][col] != 0:
                board[row][col] = 0
                removed += 1
    
    return board

def count_solutions(board, count=0):
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                for num in range(1, 10):
                    if is_valid(board, row, col, num):
                        board[row][col] = num
                        count = count_solutions(board, count)
                        board[row][col] = 0
                        if count > 1:
                            return count
                return count
    return count + 1

# =================== SudokuApp ===================
class SudokuApp(ctk.CTk):
    KITTY_IMAGE_FILE = "hello_kitty_sticker.png"
    STICKER_CONFIG = {
        "menu_main": {"size": (200, 200), "fallback_url": "https://i.imgur.com/k9b6m6i.png"},
        "game_main": {"size": (120, 120), "fallback_url": "https://i.imgur.com/k9b6m6i.png"},
        "level_select": {"size": (150, 150), "fallback_url": "https://i.imgur.com/k9b6m6i.png"},
    }
    sticker_images = {}

    def __init__(self):
        super().__init__()

        self.title("🎀 Sudoku Hello Kitty VIP Edition 🎀")

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        if screen_width < 1000 or screen_height < 900:
            self.window_width = min(900, screen_width - 50)
            self.window_height = min(750, screen_height - 100)
            self.cell_size = max(30, int(self.window_width * 0.045))
            self.font_size = max(14, int(self.window_width * 0.017))
        else:
            self.window_width = 900
            self.window_height = 850
            self.cell_size = 45
            self.font_size = 20

        self.geometry(f"{self.window_width}x{self.window_height}")
        self.resizable(True, True)
        
        x = (screen_width - self.window_width) // 2
        y = (screen_height - self.window_height) // 2
        self.geometry(f"+{x}+{y}")

        self.config(bg=KITTY_BG)
        ctk.set_appearance_mode("light")

        # Khởi tạo các manager mới
        self.db = DatabaseManager()
        self.audio_manager = AudioManager()
        self.audio_manager.load_sounds()  # Tải âm thanh
        
        # Biến trạng thái mới
        self.current_user = None
        self.user_id = None
        self.game_mode = "single"  # single, ai_battle, multiplayer
        self.ai_opponent = None
        self.ai_score = 0
        self.player_score = 0

        # Biến gốc
        self.board = None
        self.cells = []
        self.solution = None
        self.time_elapsed = 0
        self.timer_id = None
        self.current_difficulty = "Medium"
        self.selected_cell = None
        self.cell_colors = {}
        self.is_paused = False
        self.pause_button = None
        self.pause_overlay = None
        self.hint_count = 5
        self.hint_button = None
        self.hint_label = None
        self.sudoku_container = None
        self.score = 0
        self.score_label = None
        self.correct_moves = 0
        self.incorrect_moves = 0
        self.scored_cells = set()
        self.initial_board = None
        self.numpad_buttons = []
        self.numpad_clear_btn = None
        self.timer_label = None

        # THÊM BIẾN CHO ĐẤU MÁY
        self.ai_timer_id = None
        self.ai_moves = 0
        self.ai_correct_moves = 0
        self.ai_wrong_moves = 0
        self.battle_time_limit = 300  # 5 phút
        self.player_score_label = None
        self.ai_score_label = None
        self.battle_timer_label = None

        self.load_all_stickers()
        self.show_main_menu()

    def load_all_stickers(self):
        for name, config in self.STICKER_CONFIG.items():
            image_source = self.KITTY_IMAGE_FILE
            size_factor = min(self.window_width / 900, self.window_height / 850)
            adjusted_size = (
                int(config["size"][0] * size_factor),
                int(config["size"][1] * size_factor)
            )
            self.sticker_images[name] = self.load_single_sticker(
                source=image_source,
                size=adjusted_size,
                fallback_url=config["fallback_url"]
            )

    def load_single_sticker(self, source, size, fallback_url):
        if os.path.exists(source):
            try:
                local_image = Image.open(source).resize(size)
                return ctk.CTkImage(light_image=local_image, dark_image=local_image, size=size)
            except Exception:
                source = fallback_url
        else:
            source = fallback_url
        try:
            image_bytes = urlopen(source).read()
            fallback_image = Image.open(io.BytesIO(image_bytes)).resize(size)
            return ctk.CTkImage(light_image=fallback_image, dark_image=fallback_image, size=size)
        except Exception:
            tk_image = Image.new('RGB', size, color=KITTY_ACCENT_PINK)
            return ctk.CTkImage(light_image=tk_image, dark_image=tk_image, size=size)

    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.pause_overlay = None

    def format_time(self, seconds):
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def stop_timer(self):
        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None

    def update_timer(self):
        if not self.is_paused:
            self.time_elapsed += 1
            if hasattr(self, 'timer_label') and self.timer_label:
                self.timer_label.configure(text=self.format_time(self.time_elapsed))
        self.timer_id = self.after(1000, self.update_timer)

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        
        if self.is_paused:
            self.audio_manager.play_sound('pause')
            self.stop_timer()
            # THÊM: Dừng AI timer
            if self.ai_timer_id:
                self.after_cancel(self.ai_timer_id)
            self.pause_button.configure(text="▶️ Resume")
            for i in range(9):
                for j in range(9):
                    if self.initial_board[i][j] == 0:
                        self.cells[i][j].configure(state="disabled")
            self.enable_numpad(False)
            if self.hint_button:
                self.hint_button.configure(state="disabled")
            self.show_pause_overlay()
        else:
            self.audio_manager.play_sound('click')
            self.pause_button.configure(text="⏸️ Pause")
            for i in range(9):
                for j in range(9):
                    if self.initial_board[i][j] == 0:
                        self.cells[i][j].configure(state="normal")
            self.enable_numpad(True)
            if self.hint_button and self.hint_count > 0:
                self.hint_button.configure(state="normal")
            # THÊM: Khởi động lại AI timer nếu là đấu máy
            if self.game_mode == "ai_battle" and not self.ai_timer_id:
                self.start_ai_turn()
            self.hide_pause_overlay()
            self.update_timer()

    def show_pause_overlay(self):
        self.hide_pause_overlay()
        
        if not self.sudoku_container or not self.sudoku_container.winfo_exists():
            return
            
        self.pause_overlay = ctk.CTkFrame(
            self.sudoku_container,
            fg_color=KITTY_MAIN_PINK, 
            corner_radius=15,
            border_width=5,
            border_color=KITTY_ACCENT_PINK
        )
        
        self.pause_overlay.place(relx=0.5, rely=0.5, anchor="center", 
                               relwidth=1, relheight=1)
        
        pause_label = ctk.CTkLabel(
            self.pause_overlay,
            text="⏸️ GAME PAUSED ⏸️",
            font=("Arial Black", max(24, int(self.window_width * 0.03)), "bold"),
            text_color="white"
        )
        pause_label.place(relx=0.5, rely=0.4, anchor="center")
        
        instruction_label = ctk.CTkLabel(
            self.pause_overlay,
            text="Click '▶️ Resume' to continue playing",
            font=("Comic Sans MS", max(14, int(self.window_width * 0.015))),
            text_color="white"
        )
        instruction_label.place(relx=0.5, rely=0.5, anchor="center")
        
        if "game_main" in self.sticker_images:
            sticker_label = ctk.CTkLabel(
                self.pause_overlay,
                image=self.sticker_images["game_main"],
                text=""
            )
            sticker_label.place(relx=0.5, rely=0.65, anchor="center")

    def hide_pause_overlay(self):
        if self.pause_overlay:
            if self.pause_overlay.winfo_exists():
                self.pause_overlay.destroy()
            self.pause_overlay = None

    def enable_numpad(self, enable):
        state = "normal" if enable else "disabled"
        for btn in self.numpad_buttons:
            btn.configure(state=state)
        if self.numpad_clear_btn:
            self.numpad_clear_btn.configure(state=state)

    def calculate_score(self):
        difficulty_bonus = {
            "Easy": 100,
            "Medium": 200,
            "Hard": 300,
            "Expert": 500
        }
        
        base_score = difficulty_bonus.get(self.current_difficulty, 100)
        time_bonus = max(0, 300 - self.time_elapsed)
        correct_move_bonus = self.correct_moves * 10
        incorrect_move_penalty = self.incorrect_moves * 5
        hint_bonus = self.hint_count * 20
        
        total_score = base_score + time_bonus + correct_move_bonus - incorrect_move_penalty + hint_bonus
        
        return max(0, total_score)

    def update_score(self):
        if self.score_label:
            self.score_label.configure(text=f"{self.score} ⭐")

    def add_score(self, points, reason=""):
        old_score = self.score
        self.score += points
        if self.score < 0:
            self.score = 0
        self.update_score()
        
        if points != 0 and reason:
            self.show_score_popup(points, reason)

    def show_score_popup(self, points, reason):
        color = "#00AA00" if points > 0 else "#FF4444"
        symbol = "+" if points > 0 else ""
        
        popup = ctk.CTkLabel(
            self,
            text=f"{symbol}{points} ⭐\n{reason}",
            font=("Comic Sans MS", max(12, int(self.window_width * 0.012)), "bold"),
            text_color=color,
            fg_color=KITTY_ACCENT_PINK,
            corner_radius=10
        )
        
        popup.place(relx=0.85, rely=0.55, anchor="center")
        
        self.after(2000, lambda: popup.destroy() if popup.winfo_exists() else None)

    # =================== MENU CHÍNH MỚI ===================
    def show_main_menu(self):
        self.clear_screen()
        self.configure(fg_color=KITTY_BG)
        self.stop_timer()
        self.is_paused = False
        self.hide_pause_overlay()

        padx_value = max(40, int(self.window_width * 0.1))
        pady_value = max(40, int(self.window_height * 0.1))
        title_font_size = max(24, int(self.window_width * 0.05))
        button_font_size = max(16, int(self.window_width * 0.02))

        main_frame = ctk.CTkFrame(
            self, fg_color=KITTY_ACCENT_PINK, corner_radius=20,
            border_width=5, border_color=KITTY_MAIN_PINK
        )
        main_frame.pack(expand=True, padx=padx_value, pady=pady_value)

        title = ctk.CTkLabel(
            main_frame, text="🌸 SUDOKU HELLO KITTY 🌸",
            font=("Arial Black", title_font_size, "bold"), text_color=KITTY_MAIN_PINK
        )
        title.pack(pady=(30, 10))

        subtitle = ctk.CTkLabel(
            main_frame, text="Nhóm 10", font=("Comic Sans MS", max(14, int(title_font_size * 0.45))),
            text_color=KITTY_TEXT
        )
        subtitle.pack(pady=(0, 20))

        # Hiển thị thông tin user nếu đã đăng nhập
        if self.current_user:
            user_label = ctk.CTkLabel(
                main_frame, text=f"👤 {self.current_user}",
                font=("Arial", max(14, int(title_font_size * 0.4)), "bold"),
                text_color=KITTY_MAIN_PINK
            )
            user_label.pack(pady=(0, 10))

        menu_sticker_img = self.sticker_images.get("menu_main")
        if menu_sticker_img:
            ctk.CTkLabel(main_frame, image=menu_sticker_img, text="").pack(pady=15)

        play_button = ctk.CTkButton(
            main_frame, text="▶️ Start Game", fg_color=KITTY_MAIN_PINK,
            hover_color=KITTY_PURPLE_HOVER, font=("Arial Black", button_font_size, "bold"),
            text_color=KITTY_BG, command=self.show_game_mode_selection,
            width=max(250, int(self.window_width * 0.4)), 
            height=max(50, int(self.window_height * 0.06)), 
            corner_radius=18,
            border_width=3, border_color="#FFFFFF"
        )
        play_button.pack(pady=(20, 15), padx=20)

        # Nút đăng nhập/đăng ký
        if not self.current_user:
            auth_button = ctk.CTkButton(
                main_frame, text="🔐 Login/Register", fg_color=KITTY_PURPLE_HOVER,
                hover_color=KITTY_MAIN_PINK, font=("Comic Sans MS", max(14, int(button_font_size * 0.7)), "bold"),
                text_color=KITTY_BG, command=self.show_login_register,
                width=max(200, int(self.window_width * 0.3)),
                height=max(40, int(self.window_height * 0.05)), 
                corner_radius=12
            )
            auth_button.pack(pady=(0, 10))
        else:
            logout_button = ctk.CTkButton(
                main_frame, text="🚪 Logout", fg_color="#CC0000",
                hover_color="#AA0000", font=("Comic Sans MS", max(14, int(button_font_size * 0.7)), "bold"),
                text_color=KITTY_BG, command=self.logout,
                width=max(200, int(self.window_width * 0.3)),
                height=max(40, int(self.window_height * 0.05)), 
                corner_radius=12
            )
            logout_button.pack(pady=(0, 10))

        # Nút cài đặt âm thanh
        sound_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        sound_frame.pack(pady=(0, 10))
        
        music_btn = ctk.CTkButton(
            sound_frame, text="🎵 Music: ON" if self.audio_manager.music_enabled else "🎵 Music: OFF",
            fg_color=KITTY_MAIN_PINK if self.audio_manager.music_enabled else KITTY_TEXT,
            command=self.toggle_music,
            width=120, height=35
        )
        music_btn.pack(side="left", padx=5)
        
        sound_btn = ctk.CTkButton(
            sound_frame, text="🔊 Sound: ON" if self.audio_manager.sound_enabled else "🔊 Sound: OFF",
            fg_color=KITTY_MAIN_PINK if self.audio_manager.sound_enabled else KITTY_TEXT,
            command=self.toggle_sound,
            width=120, height=35
        )
        sound_btn.pack(side="left", padx=5)

        quit_button = ctk.CTkButton(
            main_frame, text="❌ Exit Game", fg_color="#CC0000",
            hover_color="#AA0000", font=("Comic Sans MS", max(14, int(button_font_size * 0.7)), "bold"),
            text_color=KITTY_BG, command=self.quit,
            width=max(250, int(self.window_width * 0.4)),
            height=max(40, int(self.window_height * 0.05)), 
            corner_radius=12
        )
        quit_button.pack(pady=(0, 30))

    def toggle_music(self):
        enabled = self.audio_manager.toggle_music()
        self.show_main_menu()  # Refresh để cập nhật nút

    def toggle_sound(self):
        enabled = self.audio_manager.toggle_sound()
        self.show_main_menu()  # Refresh để cập nhật nút

    def show_login_register(self):
        """Hiển thị cửa sổ đăng nhập/đăng ký"""
        login_window = ctk.CTkToplevel(self)
        login_window.title("Đăng nhập / Đăng ký")
        login_window.geometry("400x500")
        login_window.resizable(False, False)
        login_window.transient(self)
        login_window.grab_set()
        
        # Center the window
        login_window.update_idletasks()
        x = (self.winfo_screenwidth() - login_window.winfo_width()) // 2
        y = (self.winfo_screenheight() - login_window.winfo_height()) // 2
        login_window.geometry(f"+{x}+{y}")
        
        tab_view = ctk.CTkTabview(login_window)
        tab_view.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Tab đăng nhập
        login_tab = tab_view.add("Đăng nhập")
        self.create_login_form(login_tab, login_window)
        
        # Tab đăng ký
        register_tab = tab_view.add("Đăng ký")
        self.create_register_form(register_tab, login_window)

    def create_login_form(self, parent, window):
        ctk.CTkLabel(parent, text="Tên đăng nhập:", 
                    font=("Arial", 14)).pack(pady=10)
        username_entry = ctk.CTkEntry(parent, width=200)
        username_entry.pack(pady=5)
        
        ctk.CTkLabel(parent, text="Mật khẩu:", 
                    font=("Arial", 14)).pack(pady=10)
        password_entry = ctk.CTkEntry(parent, show="*", width=200)
        password_entry.pack(pady=5)
        
        def login():
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            
            if not username or not password:
                messagebox.showerror("Lỗi", "Vui lòng điền đầy đủ thông tin!")
                return
                
            success, result = self.db.login_user(username, password)
            if success:
                self.current_user = username
                self.user_id = result
                messagebox.showinfo("Thành công", "Đăng nhập thành công!")
                window.destroy()
                self.show_main_menu()
            else:
                messagebox.showerror("Lỗi", result)
    
        login_btn = ctk.CTkButton(parent, text="Đăng nhập", 
                                 command=login, width=200)
        login_btn.pack(pady=20)

    def create_register_form(self, parent, window):
        ctk.CTkLabel(parent, text="Tên đăng nhập:", 
                    font=("Arial", 14)).pack(pady=10)
        username_entry = ctk.CTkEntry(parent, width=200)
        username_entry.pack(pady=5)
        
        ctk.CTkLabel(parent, text="Mật khẩu:", 
                    font=("Arial", 14)).pack(pady=10)
        password_entry = ctk.CTkEntry(parent, show="*", width=200)
        password_entry.pack(pady=5)
        
        ctk.CTkLabel(parent, text="Xác nhận mật khẩu:", 
                    font=("Arial", 14)).pack(pady=10)
        confirm_password_entry = ctk.CTkEntry(parent, show="*", width=200)
        confirm_password_entry.pack(pady=5)
        
        def register():
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            confirm_password = confirm_password_entry.get().strip()
            
            if not username or not password:
                messagebox.showerror("Lỗi", "Vui lòng điền đầy đủ thông tin!")
                return
                
            if password != confirm_password:
                messagebox.showerror("Lỗi", "Mật khẩu xác nhận không khớp!")
                return
                
            success, message = self.db.register_user(username, password)
            if success:
                messagebox.showinfo("Thành công", message)
                # Tự động đăng nhập sau khi đăng ký
                self.current_user = username
                success, result = self.db.login_user(username, password)
                if success:
                    self.user_id = result
                window.destroy()
                self.show_main_menu()
            else:
                messagebox.showerror("Lỗi", message)
    
        register_btn = ctk.CTkButton(parent, text="Đăng ký", 
                                    command=register, width=200)
        register_btn.pack(pady=20)

    def logout(self):
        """Đăng xuất"""
        self.current_user = None
        self.user_id = None
        self.show_main_menu()

    def show_game_mode_selection(self):
        """Hiển thị màn hình chọn chế độ chơi"""
        self.clear_screen()
        
        main_frame = ctk.CTkFrame(
            self, fg_color=KITTY_ACCENT_PINK, corner_radius=20,
            border_width=5, border_color=KITTY_MAIN_PINK
        )
        main_frame.pack(expand=True, padx=40, pady=40)

        title = ctk.CTkLabel(
            main_frame, text="🎀 Select Game Mode 🎀",
            font=("Arial Black", 24, "bold"), text_color=KITTY_MAIN_PINK
        )
        title.pack(pady=(30, 20))

        # Các chế độ chơi
        modes = [
            ("🌸 Single Player", self.show_level_selection),
            ("🤖 AI Battle", self.show_ai_battle_menu),
            ("👥  Multiplayer", self.show_multiplayer_menu),
            ("🏆 Leaderboard", self.show_leaderboard)
        ]

        for text, command in modes:
            btn = ctk.CTkButton(
                main_frame, text=text,
                fg_color=KITTY_MAIN_PINK,
                hover_color=KITTY_PURPLE_HOVER,
                font=("Arial Black", 16, "bold"),
                text_color=KITTY_BG,
                command=command,
                width=250, height=50,
                corner_radius=15
            )
            btn.pack(pady=10)

        back_btn = ctk.CTkButton(
            main_frame, text="🔙 Back",
            fg_color="#CC0000", command=self.show_main_menu
        )
        back_btn.pack(pady=20)

    def show_ai_battle_menu(self):
        """Hiển thị menu đấu với AI"""
        if not self.current_user:
            self.show_login_register()
            return
        
        self.clear_screen()
        
        main_frame = ctk.CTkFrame(
            self, fg_color=KITTY_ACCENT_PINK, corner_radius=20
        )
        main_frame.pack(expand=True, padx=40, pady=40)
        
        ctk.CTkLabel(
            main_frame, text="🤖 Challange Mode AI",
            font=("Arial Black", 24, "bold")
        ).pack(pady=20)
        
        ai_levels = [
            ("🐣 AI Easy", "Easy"),
            ("🎯 AI Medium", "Medium"), 
            ("🔥 AI Hard", "Hard"),
            ("👑 AI Expert", "Expert")
        ]
        
        for text, level in ai_levels:
            btn = ctk.CTkButton(
                main_frame, text=text,
                command=lambda l=level: self.start_ai_game(l),
                width=200, height=45
            )
            btn.pack(pady=10)
        
        ctk.CTkButton(
            main_frame, text="🔙 Back", 
            command=self.show_game_mode_selection
        ).pack(pady=20)

    def start_ai_game(self, ai_level):
        """Bắt đầu game đấu với AI"""
        self.ai_opponent = AIOpponent(ai_level)
        self.game_mode = "ai_battle"
        self.ai_score = 0
        self.player_score = 0
        self.current_difficulty = "Medium"  # Độ khó bàn chơi
        self.show_game()

    def show_multiplayer_menu(self):
        """Hiển thị menu multiplayer"""
        if not self.current_user:
            self.show_login_register()
            return
            
        self.clear_screen()
        
        main_frame = ctk.CTkFrame(
            self, fg_color=KITTY_ACCENT_PINK, corner_radius=20
        )
        main_frame.pack(expand=True, padx=40, pady=40)
        
        ctk.CTkLabel(
            main_frame, text="👥 Đấu Online",
            font=("Arial Black", 24, "bold")
        ).pack(pady=20)
        
        # Thông báo tính năng đang phát triển
        ctk.CTkLabel(
            main_frame, 
            text="Tính năng đang phát triển!\nSẽ có trong phiên bản tiếp theo.",
            font=("Arial", 14),
            text_color=KITTY_TEXT
        ).pack(pady=20)
        
        ctk.CTkButton(
            main_frame, text="🔙 Back", 
            command=self.show_game_mode_selection
        ).pack(pady=20)

    def show_leaderboard(self):
        """Hiển thị bảng xếp hạng"""
        self.clear_screen()
        
        tab_view = ctk.CTkTabview(self)
        tab_view.pack(expand=True, fill="both", padx=20, pady=20)
        
        levels = ["Easy", "Medium", "Hard", "Expert", "Tổng hợp"]
        
        for level in levels:
            tab_view.add(level)
        
        for level in levels:
            frame = tab_view.tab(level)
            
            # Lấy dữ liệu từ database
            if level == "Tổng hợp":
                leaderboard_data = self.db.get_leaderboard(limit=10)
            else:
                leaderboard_data = self.db.get_leaderboard(level, 10)
            
            # Hiển thị bảng xếp hạng
            if not leaderboard_data:
                ctk.CTkLabel(
                    frame, 
                    text="Chưa có dữ liệu!",
                    font=("Arial", 16),
                    text_color=KITTY_TEXT
                ).pack(pady=50)
                continue
                
            for i, player in enumerate(leaderboard_data):
                self.create_leaderboard_row(frame, player, i)
        
        ctk.CTkButton(
            self, text="🔙 Back", 
            command=self.show_game_mode_selection
        ).pack(pady=10)

    def create_leaderboard_row(self, parent, player, rank):
        """Tạo một dòng trong bảng xếp hạng"""
        rank_color = "#FFD700" if rank == 0 else "#C0C0C0" if rank == 1 else "#CD7F32" if rank == 2 else KITTY_TEXT
        
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", padx=10, pady=2)
        
        # Xếp hạng
        ctk.CTkLabel(
            row_frame, text=f"{rank + 1}.",
            text_color=rank_color, font=("Arial", 14, "bold"),
            width=30
        ).pack(side="left")
        
        # Tên người chơi
        ctk.CTkLabel(
            row_frame, text=player['username'],
            text_color=rank_color, font=("Arial", 14),
            width=150
        ).pack(side="left", padx=5)
        
        # Điểm số
        ctk.CTkLabel(
            row_frame, text=f"{player['score']} pts",
            text_color=rank_color, font=("Arial", 14, "bold"),
            width=80
        ).pack(side="left", padx=5)
        
        # Tỷ lệ thắng (nếu có)
        if 'win_rate' in player:
            ctk.CTkLabel(
                row_frame, text=f"{player['win_rate']}%",
                text_color=rank_color, font=("Arial", 12),
                width=60
            ).pack(side="right", padx=5)

    # =================== LEVEL SELECTION ===================
    def show_level_selection(self):
        self.clear_screen()
        self.configure(fg_color=KITTY_BG)
        self.stop_timer()
        self.is_paused = False
        self.hide_pause_overlay()

        padx_value = max(40, int(self.window_width * 0.1))
        pady_value = max(40, int(self.window_height * 0.1))
        title_font_size = max(24, int(self.window_width * 0.05))
        button_font_size = max(16, int(self.window_width * 0.02))

        main_frame = ctk.CTkFrame(
            self, fg_color=KITTY_ACCENT_PINK, corner_radius=20,
            border_width=5, border_color=KITTY_MAIN_PINK
        )
        main_frame.pack(expand=True, padx=padx_value, pady=pady_value)

        title = ctk.CTkLabel(
            main_frame, text="🎀 Select Difficulty 🎀",
            font=("Arial Black", title_font_size, "bold"), text_color=KITTY_MAIN_PINK
        )
        title.pack(pady=(30, 10))

        level_sticker_img = self.sticker_images.get("level_select")
        if level_sticker_img:
            ctk.CTkLabel(main_frame, image=level_sticker_img, text="").pack(pady=15)

        levels_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        levels_frame.pack(expand=True, fill="both", pady=20)
        
        levels_frame.grid_columnconfigure(0, weight=1)
        for i in range(5):
            levels_frame.grid_rowconfigure(i, weight=1)

        difficulty_levels = ["🌸 Easy", "🎀 Medium", "✨ Hard", "👑 Expert"]

        for i, level_name in enumerate(difficulty_levels):
            level_button = ctk.CTkButton(
                levels_frame, 
                text=level_name,
                fg_color=KITTY_MAIN_PINK,
                hover_color=KITTY_PURPLE_HOVER, 
                font=("Arial Black", button_font_size, "bold"),
                text_color=KITTY_BG, 
                command=lambda l=level_name.split()[-1]: self.start_game_with_level(l),
                width=max(250, int(self.window_width * 0.4)), 
                height=max(50, int(self.window_height * 0.06)), 
                corner_radius=15,
                border_width=2, 
                border_color="#FFFFFF"
            )
            level_button.grid(row=i, column=0, padx=20, pady=8, sticky="nsew")

        back_button = ctk.CTkButton(
            levels_frame, text="🔙 Back", fg_color="#CC0000",
            hover_color="#AA0000", font=("Comic Sans MS", max(14, int(button_font_size * 0.7)), "bold"),
            text_color=KITTY_BG, command=self.show_game_mode_selection,
            width=max(200, int(self.window_width * 0.3)),
            height=max(40, int(self.window_height * 0.05)), 
            corner_radius=12
        )
        back_button.grid(row=4, column=0, padx=20, pady=(15, 0), sticky="nsew")

    def start_game_with_level(self, level):
        self.current_difficulty = level
        self.show_game()

    # =================== GAME ===================
    def show_game(self):
        self.clear_screen()
        self.configure(fg_color=KITTY_BG)
        self.stop_timer()
        self.time_elapsed = 0
        self.selected_cell = None
        self.cell_colors = {}
        self.is_paused = False
        self.hint_count = 5
        self.score = 0
        self.correct_moves = 0
        self.incorrect_moves = 0
        self.scored_cells = set()
        self.hide_pause_overlay()

        # Reset AI nếu là đấu máy
        if self.game_mode == "ai_battle" and self.ai_opponent:
            self.ai_opponent.reset_ai()
            self.ai_score = 0
            self.player_score = 0

        self.board = generate_board(self.current_difficulty)
        self.initial_board = [row[:] for row in self.board]
        self.solution = [row[:] for row in self.board]
        solve_board(self.solution)

        header_font_size = max(18, int(self.window_width * 0.03))
        button_font_size = max(14, int(self.window_width * 0.018))

        header_frame = ctk.CTkFrame(self, fg_color=KITTY_ACCENT_PINK, corner_radius=15)
        header_frame.pack(pady=(15, 10), padx=max(20, int(self.window_width * 0.05)), fill='x')
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=1)
        header_frame.grid_columnconfigure(2, weight=1)
        header_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(
            header_frame, text="Sudoku Challenge",
            font=("Arial Black", header_font_size, "bold"), text_color=KITTY_MAIN_PINK
        ).grid(row=0, column=0, sticky='w', padx=15, pady=8)

        difficulty_label = ctk.CTkLabel(
            header_frame, text=f"Level: {self.current_difficulty}",
            font=("Arial Black", max(14, int(header_font_size * 0.8)), "bold"), text_color=KITTY_TEXT
        )
        difficulty_label.grid(row=0, column=1, padx=15, pady=8)

        self.timer_label = ctk.CTkLabel(
            header_frame, text=self.format_time(self.time_elapsed),
            font=("Arial Black", header_font_size, "bold"), text_color=KITTY_TEXT
        )
        self.timer_label.grid(row=0, column=2, sticky='e', padx=15, pady=8)

        self.hint_label = ctk.CTkLabel(
            header_frame, text=f"💡 Hints: {self.hint_count}",
            font=("Arial Black", max(14, int(header_font_size * 0.8)), "bold"), 
            text_color=KITTY_MAIN_PINK
        )
        self.hint_label.grid(row=0, column=3, sticky='e', padx=15, pady=8)

        # THÊM: Giao diện đấu máy
        if self.game_mode == "ai_battle":
            self.create_battle_ui(header_frame)

        main_grid_frame = ctk.CTkFrame(self, fg_color=KITTY_BG)
        main_grid_frame.pack(pady=(10, 15), padx=15)
        main_grid_frame.grid_columnconfigure(0, weight=0)
        main_grid_frame.grid_columnconfigure(1, weight=0)

        self.sudoku_container = ctk.CTkFrame(main_grid_frame, fg_color=KITTY_MAIN_PINK, corner_radius=15)
        self.sudoku_container.grid(row=0, column=0, padx=(0, 20), sticky="n")

        grid_frame = ctk.CTkFrame(self.sudoku_container, fg_color=KITTY_BG, corner_radius=10)
        grid_frame.pack(padx=6, pady=6)

        self.cells = []
        for i in range(9):
            row_cells = []
            row_block_frame = ctk.CTkFrame(
                grid_frame,
                fg_color="transparent",
                border_width=3 if i % 3 == 0 and i != 0 else 0,
                border_color=KITTY_MAIN_PINK
            )
            row_block_frame.grid(row=i, column=0, columnspan=9, sticky="ew")
            row_block_frame.grid_columnconfigure(tuple(range(9)), weight=1)
            row_block_frame.grid_rowconfigure(0, weight=1)

            for j in range(9):
                value = self.initial_board[i][j]
                block_color = KITTY_BG if (i // 3 + j // 3) % 2 == 0 else KITTY_BG_ALT

                entry = ctk.CTkEntry(
                    row_block_frame,
                    width=self.cell_size,
                    height=self.cell_size,
                    justify="center",
                    font=("Comic Sans MS", self.font_size, "bold"),
                    fg_color=block_color if value == 0 else KITTY_ACCENT_PINK,
                    text_color="#000000" if value == 0 else KITTY_TEXT,
                    border_width=1,
                    corner_radius=5,
                    border_color=KITTY_MAIN_PINK if (j + 1) % 3 == 0 and j != 8 else KITTY_ACCENT_PINK
                )

                entry.grid(row=0, column=j, padx=(1, 1), pady=1)

                if value != 0:
                    entry.insert(0, str(value))
                    entry.configure(state="disabled", text_color=KITTY_MAIN_PINK)
                    self.cell_colors[(i, j)] = KITTY_ACCENT_PINK
                else:
                    entry.bind("<KeyRelease>", lambda e, r=i, c=j: self.validate_input(r, c))
                    entry.bind("<Button-1>", lambda e, r=i, c=j: self.select_cell(r, c))
                    entry.configure(text_color="#000000")
                    self.cell_colors[(i, j)] = block_color

                row_cells.append(entry)

            row_block_frame.grid(row=i, column=0, columnspan=9, sticky="ew",
                                 pady=(3 if i % 3 == 0 and i != 0 else 1, 1))
            self.cells.append(row_cells)

        right_panel = ctk.CTkFrame(main_grid_frame, fg_color=KITTY_BG)
        right_panel.grid(row=0, column=1, padx=(0, 15), sticky="nw", pady=30)

        sticker_score_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        sticker_score_frame.pack(pady=(0, 15), anchor='w')

        game_main_img = self.sticker_images.get("game_main")
        if game_main_img:
            sticker_size = max(100, int(self.window_width * 0.15))
            sticker_frame = ctk.CTkFrame(sticker_score_frame, fg_color=KITTY_ACCENT_PINK, 
                                       corner_radius=15, width=sticker_size, height=sticker_size)
            sticker_frame.pack(side="left", padx=(0, 10))
            sticker_frame.grid_propagate(False)

            sticker1 = ctk.CTkLabel(sticker_frame, image=game_main_img, text="", fg_color="transparent")
            sticker1.place(relx=0.5, rely=0.5, anchor="center")

        score_frame = ctk.CTkFrame(sticker_score_frame, fg_color="#FFF8F8",
                                 corner_radius=12, width=75, height=75)
        score_frame.pack(side="left")
        score_frame.grid_propagate(False)
        score_frame.pack_propagate(False)

        score_text_label = ctk.CTkLabel(
            score_frame,
            text="Score",
            font=("Arial Black", max(10, int(self.window_width * 0.01)), "bold"),
            text_color=KITTY_MAIN_PINK
        )
        score_text_label.pack(pady=(8, 0))

        self.score_label = ctk.CTkLabel(
            score_frame,
            text=f"{self.score} ⭐",
            font=("Arial Black", max(14, int(self.window_width * 0.016)), "bold"),
            text_color="#FFD700"
        )
        self.score_label.pack(pady=(2, 8))

        self.create_numpad(right_panel)

        btn_frame = ctk.CTkFrame(self, fg_color=KITTY_BG)
        btn_frame.pack(pady=(10, 15))

        controls = [
            ("⏸️ Pause", self.toggle_pause, KITTY_MAIN_PINK),
            ("💡 Hint", self.handle_hint, KITTY_MAIN_PINK),
            ("🔄 New Game", self.reset_board, KITTY_MAIN_PINK),
            ("👑 Solve", self.handle_solve, KITTY_MAIN_PINK),
            ("🏠 Menu", self.show_main_menu, "#CC0000"),
        ]

        for txt, cmd, color in controls:
            b = ctk.CTkButton(
                btn_frame,
                text=txt,
                fg_color=color,
                hover_color=KITTY_PURPLE_HOVER if color == KITTY_MAIN_PINK else "#AA0000",
                font=("Comic Sans MS", button_font_size, "bold"),
                text_color=KITTY_BG,
                command=cmd,
                width=max(120, int(self.window_width * 0.15)),
                height=max(35, int(self.window_height * 0.04)),
                corner_radius=12,
                border_width=3,
                border_color=KITTY_ACCENT_PINK
            )
            b.pack(side="left", padx=8, pady=5)
            
            if txt == "⏸️ Pause":
                self.pause_button = b
            elif txt == "💡 Hint":
                self.hint_button = b

        self.update_timer()
        
        # THÊM: Bắt đầu vòng lặp AI nếu là đấu máy
        if self.game_mode == "ai_battle":
            self.start_ai_turn()

    def create_battle_ui(self, header_frame):
        """Tạo giao diện đấu máy"""
        if self.game_mode != "ai_battle":
            return
            
        # Frame chứa thông tin đấu máy
        battle_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        battle_frame.grid(row=1, column=0, columnspan=4, sticky="ew", padx=15, pady=5)
        
        # Điểm số người chơi
        self.player_score_label = ctk.CTkLabel(
            battle_frame,
            text=f"👤 YOU: {self.player_score} ⭐",
            font=("Arial Black", 14, "bold"),
            text_color=KITTY_MAIN_PINK
        )
        self.player_score_label.pack(side="left", padx=10)
        
        # VS
        vs_label = ctk.CTkLabel(
            battle_frame,
            text="⚡ VS ⚡",
            font=("Arial Black", 12, "bold"),
            text_color=KITTY_TEXT
        )
        vs_label.pack(side="left", padx=10)
        
        # Điểm số AI
        self.ai_score_label = ctk.CTkLabel(
            battle_frame,
            text=f"🤖 AI: {self.ai_score} ⭐",
            font=("Arial Black", 14, "bold"),
            text_color="#666666"
        )
        self.ai_score_label.pack(side="left", padx=10)
        
        # Thời gian còn lại
        self.battle_timer_label = ctk.CTkLabel(
            battle_frame,
            text=f"⏰ {self.format_time(self.battle_time_limit)}",
            font=("Arial Black", 12, "bold"),
            text_color=KITTY_MAIN_PINK
        )
        self.battle_timer_label.pack(side="right", padx=10)

    def create_numpad(self, parent):
        numpad_frame = ctk.CTkFrame(parent, fg_color=KITTY_ACCENT_PINK, corner_radius=15)
        numpad_frame.pack(pady=(0, 10), anchor='w')
        
        numpad_title = ctk.CTkLabel(
            numpad_frame, 
            text="🎀 Number Pad 🎀",
            font=("Arial Black", max(14, int(self.window_width * 0.015)), "bold"),
            text_color=KITTY_MAIN_PINK
        )
        numpad_title.grid(row=0, column=0, columnspan=3, pady=(10, 5))
        
        self.numpad_buttons = []
        for i in range(3):
            for j in range(3):
                num = i * 3 + j + 1
                btn = ctk.CTkButton(
                    numpad_frame,
                    text=str(num),
                    width=max(35, int(self.window_width * 0.04)),
                    height=max(35, int(self.window_height * 0.04)),
                    font=("Arial Black", max(14, int(self.window_width * 0.015))),
                    fg_color=KITTY_MAIN_PINK,
                    hover_color=KITTY_PURPLE_HOVER,
                    text_color=KITTY_BG,
                    command=lambda n=num: self.on_numpad_click(n)
                )
                btn.grid(row=i+1, column=j, padx=3, pady=3)
                self.numpad_buttons.append(btn)
        
        self.numpad_clear_btn = ctk.CTkButton(
            numpad_frame,
            text="❌ Clear",
            width=max(35, int(self.window_width * 0.04)),
            height=max(35, int(self.window_height * 0.04)),
            font=("Arial Black", max(12, int(self.window_width * 0.012))),
            fg_color=KITTY_ERROR_RED,
            hover_color="#AA0000",
            text_color=KITTY_BG,
            command=self.on_clear_click
        )
        self.numpad_clear_btn.grid(row=4, column=0, columnspan=3, padx=3, pady=5, sticky="ew")

    def select_cell(self, row, col):
        if self.selected_cell:
            prev_row, prev_col = self.selected_cell
            self.cells[prev_row][prev_col].configure(fg_color=self.cell_colors.get((prev_row, prev_col), KITTY_BG))
        
        self.selected_cell = (row, col)
        self.cells[row][col].configure(fg_color=KITTY_PURPLE_HOVER)

    def on_numpad_click(self, number):
        self.audio_manager.play_sound('click')
        if not self.selected_cell:
            messagebox.showinfo("Select Cell", "Please select a cell first!")
            return
            
        row, col = self.selected_cell
        
        # CHO PHÉP SỬA CẢ Ô AI (chỉ cần không phải ô gốc)
        if self.initial_board[row][col] != 0:
            messagebox.showinfo("Invalid Cell", "This cell cannot be modified!")
            return
            
        self.cells[row][col].delete(0, "end")
        self.cells[row][col].insert(0, str(number))
        
        self.validate_input(row, col)

    def on_clear_click(self):
        self.audio_manager.play_sound('click')
        if not self.selected_cell:
            messagebox.showinfo("Select Cell", "Please select a cell first!")
            return
            
        row, col = self.selected_cell
        
        # CHO PHÉP XÓA CẢ Ô AI (chỉ cần không phải ô gốc)
        if self.initial_board[row][col] != 0:
            messagebox.showinfo("Invalid Cell", "This cell cannot be modified!")
            return
            
        self.cells[row][col].delete(0, "end")
        
        # Reset màu về màu nền block
        block_color = KITTY_BG if (row // 3 + col // 3) % 2 == 0 else KITTY_BG_ALT
        self.cell_colors[(row, col)] = block_color
        self.cells[row][col].configure(fg_color=block_color, text_color="#000000")

    # ========== PHƯƠNG THỨC ĐẤU MÁY MỚI ==========
    def start_ai_turn(self):
        """Bắt đầu lượt đi của AI"""
        if self.game_mode != "ai_battle" or self.is_paused:
            return
            
        # Kiểm tra thời gian
        if self.time_elapsed >= self.battle_time_limit:
            self.end_ai_battle()
            return
            
        # Cập nhật timer đấu máy
        time_left = self.battle_time_limit - self.time_elapsed
        if self.battle_timer_label:
            self.battle_timer_label.configure(text=f"⏰ {self.format_time(time_left)}")
        
        # AI thực hiện nước đi
        current_board = self.get_current_board_state()
        row, col, value, is_correct = self.ai_opponent.make_move(current_board, self.solution)
        
        if row is not None:
            # Hiển thị nước đi của AI
            self.show_ai_move(row, col, value, is_correct)
            
            # Cập nhật điểm AI
            self.ai_score = self.ai_opponent.calculate_ai_score()
                
            # Cập nhật UI
            if self.ai_score_label:
                self.ai_score_label.configure(text=f"🤖 AI: {self.ai_score} ⭐")
        
        # Lặp lại sau 2-8 giây (tùy độ khó)
        delay = random.randint(2000, 8000)  # milliseconds
        self.ai_timer_id = self.after(delay, self.start_ai_turn)

    def get_current_board_state(self):
        """Lấy trạng thái bàn cờ hiện tại"""
        board_state = []
        for i in range(9):
            row = []
            for j in range(9):
                if self.initial_board[i][j] != 0:
                    row.append(self.initial_board[i][j])
                else:
                    cell_value = self.cells[i][j].get()
                    row.append(int(cell_value) if cell_value.isdigit() else 0)
            board_state.append(row)
        return board_state

    def show_ai_move(self, row, col, value, is_correct):
        """Hiển thị nước đi của AI - CHO PHÉP SỬA"""
        # Chỉ hiển thị nếu ô còn trống
        if self.cells[row][col].get() == "":
            self.cells[row][col].delete(0, "end")
            self.cells[row][col].insert(0, str(value))
            
            # Đánh dấu màu cho nước đi của AI (KHÔNG KHÓA Ô)
            if is_correct:
                self.cells[row][col].configure(
                    fg_color="#E8F4FF",  # Xanh nhạt - AI đúng
                    text_color="#0066CC"
                    # KHÔNG có state="disabled" → cho phép sửa
                )
            else:
                self.cells[row][col].configure(
                    fg_color="#FFF0F0",  # Đỏ rất nhạt - AI sai
                    text_color="#FF4444"
                    # KHÔNG có state="disabled" → cho phép sửa
                )
            
            # Đảm bảo ô vẫn có thể chỉnh sửa
            self.cells[row][col].configure(state="normal")
            
            # Gắn lại sự kiện (phòng trường hợp bị mất)
            self.cells[row][col].bind("<KeyRelease>", lambda e, r=row, c=col: self.validate_input(r, c))
            self.cells[row][col].bind("<Button-1>", lambda e, r=row, c=col: self.select_cell(r, c))
            
            # Kiểm tra thắng/thua
            self.check_ai_battle_progress()

    def check_ai_battle_progress(self):
        """Kiểm tra tiến độ đấu máy"""
        # Kiểm tra nếu bàn cờ đã đầy
        if self.is_board_completed():
            self.end_ai_battle()
            return
            
        # Kiểm tra thời gian
        if self.time_elapsed >= self.battle_time_limit:
            self.end_ai_battle()

    def is_board_completed(self):
        """Kiểm tra xem bàn cờ đã được điền hết chưa"""
        for i in range(9):
            for j in range(9):
                if self.cells[i][j].get() == "":
                    return False
        return True

    def end_ai_battle(self):
        """Kết thúc trận đấu với AI"""
        self.stop_timer()
        if self.ai_timer_id:
            self.after_cancel(self.ai_timer_id)
        
        # Xác định người thắng
        if self.player_score > self.ai_score:
            winner = "player"
            result_text = "🎉 BẠN THẮNG! 🎉"
        elif self.ai_score > self.player_score:
            winner = "ai"  
            result_text = "🤖 AI THẮNG! 🤖"
        else:
            winner = "draw"
            result_text = "🤝 HÒA! 🤝"
        
        # Hiển thị kết quả
        messagebox.showinfo(
            "Kết thúc đấu máy!",
            f"{result_text}\n\n"
            f"Điểm của bạn: {self.player_score} ⭐\n"
            f"Điểm AI: {self.ai_score} ⭐\n"
            f"Thời gian: {self.format_time(self.time_elapsed)}\n\n"
            f"{'Bạn xuất sắc! 🌟' if winner == 'player' else 'Cố gắng lần sau! 💪' if winner == 'ai' else 'Trận đấu cân bằng! ⚖️'}"
        )
        
        # Cập nhật database
        if self.current_user and self.user_id:
            self.db.update_user_stats(
                self.user_id, 
                self.current_difficulty, 
                self.player_score, 
                self.time_elapsed, 
                won=(winner == "player")
            )

    # ========== Gameplay Functions ==========
    def is_input_incorrect(self, row, col, num):
        for i in range(9):
            if i != col and self.cells[row][i].get() == str(num):
                return True
            if i != row and self.cells[i][col].get() == str(num):
                return True

        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for r in range(start_row, start_row + 3):
            for c in range(start_col, start_col + 3):
                if r == row and c == col:
                    continue
                if self.cells[r][c].get() == str(num):
                    return True
        return False

    def reset_board(self):
        self.audio_manager.play_sound('click')
        # THÊM: Dừng AI timer nếu có
        if self.ai_timer_id:
            self.after_cancel(self.ai_timer_id)
            self.ai_timer_id = None
        self.show_game()

    def handle_hint(self):
        self.audio_manager.play_sound('hint')
        if self.is_paused:
            messagebox.showinfo("Game Paused", "Please resume the game first!")
            return
            
        if self.hint_count <= 0:
            messagebox.showinfo("No Hints Left", "You've used all 5 hints! Try solving the puzzle on your own. 🎀")
            return
            
        for i in range(9):
            for j in range(9):
                if self.cells[i][j].cget("state") != "disabled" and self.cells[i][j].get() == "":
                    self.hint_count -= 1
                    self.hint_label.configure(text=f"💡 Hints: {self.hint_count}")
                    
                    self.cells[i][j].insert(0, str(self.solution[i][j]))
                    if self.is_input_incorrect(i, j, self.solution[i][j]):
                        self.cells[i][j].configure(fg_color="#FFE8E8", text_color="#FF4444")
                        self.cell_colors[(i, j)] = "#FFE8E8"
                        self.add_score(-1, "Wrong hint!")
                    else:
                        self.cells[i][j].configure(fg_color="#E8FFE8", text_color="#00AA00")
                        self.cell_colors[(i, j)] = "#E8FFE8"
                        self.scored_cells.add((i, j))
                    
                    if self.hint_count <= 0 and self.hint_button:
                        self.hint_button.configure(state="disabled", 
                                                 fg_color=KITTY_TEXT,
                                                 hover_color=KITTY_TEXT)
                    
                    self.check_win()
                    return
        messagebox.showinfo("Sudoku", "All cells are filled! Check your solution.")

    def handle_solve(self):
        self.audio_manager.play_sound('click')
        if self.is_paused:
            messagebox.showinfo("Game Paused", "Please resume the game first!")
            return
            
        response = messagebox.askyesno("Solve Sudoku", "Are you sure you want to see the solution? The game will end.")
        if response:
            self.stop_timer()
            # THÊM: Dừng AI timer nếu có
            if self.ai_timer_id:
                self.after_cancel(self.ai_timer_id)
            for i in range(9):
                for j in range(9):
                    self.cells[i][j].configure(state="normal")
                    self.cells[i][j].delete(0, "end")
                    self.cells[i][j].insert(0, str(self.solution[i][j]))
                    self.cells[i][j].configure(state="disabled", fg_color=KITTY_ACCENT_PINK, text_color="#000000")
                    self.cell_colors[(i, j)] = KITTY_ACCENT_PINK
            messagebox.showinfo("Solution", "Congratulations! Here is the complete solution.")

    def validate_input(self, row, col):
        if self.is_paused:
            return
            
        val = self.cells[row][col].get().strip()
        block_color = KITTY_BG if (row // 3 + col // 3) % 2 == 0 else KITTY_BG_ALT

        # KIỂM TRA NẾU ĐÂY LÀ Ô AI ĐÃ ĐI
        is_ai_cell = hasattr(self, 'ai_opponent') and self.ai_opponent and (row, col) in self.ai_opponent.ai_cells

        if not val.isdigit() or not (1 <= int(val) <= 9):
            if val == "":
                self.cells[row][col].configure(fg_color=block_color, text_color="#000000")
                self.cell_colors[(row, col)] = block_color
                self.check_win()
                return

            self.cells[row][col].delete(0, "end")
            self.cells[row][col].configure(fg_color=KITTY_ERROR_RED, text_color="#CC0000")
            self.after(200, lambda: self.update_cell_color(row, col, block_color))
            return

        if len(val) > 1:
            val = val[-1]
            self.cells[row][col].delete(0, "end")
            self.cells[row][col].insert(0, val)

        num = int(val)

        if self.is_input_incorrect(row, col, num) or num != self.solution[row][col]:
            self.audio_manager.play_sound('wrong')
            self.cells[row][col].configure(fg_color="#FFE8E8", text_color="#FF4444")
            self.cell_colors[(row, col)] = "#FFE8E8"
            self.incorrect_moves += 1
            
            # XỬ LÝ ĐIỂM ĐẶC BIỆT CHO Ô AI
            if self.game_mode == "ai_battle":
                if is_ai_cell:
                    # Nếu sửa ô AI mà vẫn sai → trừ ít điểm hơn
                    self.player_score = max(0, self.player_score - 1)
                    self.add_score(-1, "Still wrong!")
                else:
                    # Ô thường sai → trừ điểm bình thường
                    self.player_score = max(0, self.player_score - 1)
                    self.add_score(-1, "Wrong move!")
                    
                if self.player_score_label:
                    self.player_score_label.configure(text=f"👤 YOU: {self.player_score} ⭐")
            else:
                self.add_score(-1, "Wrong move!")
                
        else:
            self.audio_manager.play_sound('correct')
            
            # XỬ LÝ MÀU SẮC VÀ ĐIỂM ĐẶC BIỆT CHO Ô AI
            if self.game_mode == "ai_battle" and is_ai_cell:
                # Sửa ô AI sai thành đúng → thưởng nhiều điểm và màu đặc biệt
                self.cells[row][col].configure(
                    fg_color="#E8FFE8",  # Xanh lá - đã sửa đúng
                    text_color="#00AA00"
                )
                if (row, col) not in self.scored_cells:
                    self.correct_moves += 1
                    self.player_score += 15  # Thưởng nhiều hơn vì sửa lỗi AI
                    if self.player_score_label:
                        self.player_score_label.configure(text=f"👤 YOU: {self.player_score} ⭐")
                    self.add_score(15, "Fixed AI's mistake! 🎯")
                    self.scored_cells.add((row, col))
            else:
                # Ô thường đúng → xử lý bình thường
                self.cells[row][col].configure(fg_color="#E8FFE8", text_color="#00AA00")
                self.cell_colors[(row, col)] = "#E8FFE8"
                
                if (row, col) not in self.scored_cells:
                    self.correct_moves += 1
                    if self.game_mode == "ai_battle":
                        self.player_score += 10
                        if self.player_score_label:
                            self.player_score_label.configure(text=f"👤 YOU: {self.player_score} ⭐")
                    self.add_score(10, "Correct move!")
                    self.scored_cells.add((row, col))

        self.check_win()
        #Kiểm tra đấu máy
        if self.game_mode == "ai_battle":
            self.check_ai_battle_progress()

    def update_cell_color(self, row, col, color):
        self.cells[row][col].configure(fg_color=color)
        self.cell_colors[(row, col)] = color

    def check_win(self):
        for i in range(9):
            for j in range(9):
                if self.cells[i][j].cget("state") != "disabled":
                    current_value = self.cells[i][j].get()
                    if current_value == "" or int(current_value) != self.solution[i][j]:
                        return
        
        self.audio_manager.play_sound('win')
        self.stop_timer()
        # Dừng AI timer 
        if self.ai_timer_id:
            self.after_cancel(self.ai_timer_id)
            
        final_time = self.format_time(self.time_elapsed)
        final_score = self.calculate_score()
        
        completion_bonus = 100
        self.add_score(completion_bonus, "Puzzle completed!")
        
        # Cập nhật database nếu user đã đăng nhập
        if self.current_user and self.user_id:
            self.db.update_user_stats(self.user_id, self.current_difficulty, final_score, self.time_elapsed, won=True)
        
        messagebox.showinfo("🎉 Congratulations!",
                            f"You completed the Sudoku Hello Kitty VIP Edition 🎀 in {final_time}!\n"
                            f"Level: {self.current_difficulty}\n"
                            f"Final Score: {final_score} ⭐\n"
                            f"Correct moves: {self.correct_moves}\n"
                            f"Wrong moves: {self.incorrect_moves}\n"
                            f"Hints remaining: {self.hint_count}\n"
                            f"You're amazing!")

#===================Run App=====================
if __name__ == "__main__":
    app = SudokuApp()
    app.mainloop()