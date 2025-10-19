import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import random
from PIL import Image
import io
import os
from urllib.request import urlopen
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

        self.load_all_stickers()
        self.show_menu()

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
            self.timer_label.configure(text=self.format_time(self.time_elapsed))
        self.timer_id = self.after(1000, self.update_timer)

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        
        if self.is_paused:
            self.stop_timer()
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
            self.pause_button.configure(text="⏸️ Pause")
            for i in range(9):
                for j in range(9):
                    if self.initial_board[i][j] == 0:
                        self.cells[i][j].configure(state="normal")
            self.enable_numpad(True)
            if self.hint_button and self.hint_count > 0:
                self.hint_button.configure(state="normal")
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
# =================== MENU ===================
    def show_menu(self):
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

        menu_sticker_img = self.sticker_images.get("menu_main")
        if menu_sticker_img:
            ctk.CTkLabel(main_frame, image=menu_sticker_img, text="").pack(pady=15)

        play_button = ctk.CTkButton(
            main_frame, text="▶️ Start Game", fg_color=KITTY_MAIN_PINK,
            hover_color=KITTY_PURPLE_HOVER, font=("Arial Black", button_font_size, "bold"),
            text_color=KITTY_BG, command=self.show_level_selection,
            width=max(250, int(self.window_width * 0.4)), 
            height=max(50, int(self.window_height * 0.06)), 
            corner_radius=18,
            border_width=3, border_color="#FFFFFF"
        )
        play_button.pack(pady=(20, 15), padx=20)

        quit_button = ctk.CTkButton(
            main_frame, text="❌ Exit Game", fg_color="#CC0000",
            hover_color="#AA0000", font=("Comic Sans MS", max(14, int(button_font_size * 0.7)), "bold"),
            text_color=KITTY_BG, command=self.quit,
            width=max(250, int(self.window_width * 0.4)),
            height=max(40, int(self.window_height * 0.05)), 
            corner_radius=12
        )
        quit_button.pack(pady=(0, 30))
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
            text_color=KITTY_BG, command=self.show_menu,
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
            ("🏠 Menu", self.show_menu, "#CC0000"),
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
        buttons = []
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
                buttons.append(btn)
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
        if not self.selected_cell:
            messagebox.showinfo("Select Cell", "Please select a cell first!")
            return
            
        row, col = self.selected_cell
        
        if self.cells[row][col].cget("state") == "disabled":
            messagebox.showinfo("Invalid Cell", "This cell cannot be modified!")
            return
            
        self.cells[row][col].delete(0, "end")
        self.cells[row][col].insert(0, str(number))
        
        self.validate_input(row, col)

    def on_clear_click(self):
        if not self.selected_cell:
            messagebox.showinfo("Select Cell", "Please select a cell first!")
            return
            
        row, col = self.selected_cell
        
        if self.cells[row][col].cget("state") == "disabled":
            messagebox.showinfo("Invalid Cell", "This cell cannot be modified!")
            return
            
        self.cells[row][col].delete(0, "end")
        
        block_color = KITTY_BG if (row // 3 + col // 3) % 2 == 0 else KITTY_BG_ALT
        self.cell_colors[(row, col)] = block_color
        self.cells[row][col].configure(fg_color=block_color)
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
        self.show_game()

    def handle_hint(self):
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
        if self.is_paused:
            messagebox.showinfo("Game Paused", "Please resume the game first!")
            return
            
        response = messagebox.askyesno("Solve Sudoku", "Are you sure you want to see the solution? The game will end.")
        if response:
            self.stop_timer()
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
            self.cells[row][col].configure(fg_color="#FFE8E8", text_color="#FF4444")
            self.cell_colors[(row, col)] = "#FFE8E8"
            self.incorrect_moves += 1
            self.add_score(-1, "Wrong move!")
        else:
            self.cells[row][col].configure(fg_color="#E8FFE8", text_color="#00AA00")
            self.cell_colors[(row, col)] = "#E8FFE8"
            
            if (row, col) not in self.scored_cells:
                self.correct_moves += 1
                self.add_score(10, "Correct move!")
                self.scored_cells.add((row, col))

        self.check_win()

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
        self.stop_timer()
        final_time = self.format_time(self.time_elapsed)
        final_score = self.calculate_score()
        
        completion_bonus = 100
        self.add_score(completion_bonus, "Puzzle completed!")
        
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