import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import random
from PIL import Image
import io
import os
from urllib.request import urlopen

# =================== 🎀 Bảng Màu Hello Kitty VIP 🎀 ===================
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

def generate_board():
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
        return generate_board()
    solved_board = [row[:] for row in board]
    cells_to_remove = 40
    while cells_to_remove > 0:
        row, col = random.randint(0, 8), random.randint(0, 8)
        if board[row][col] != 0:
            board[row][col] = 0
            cells_to_remove -= 1
    return board

# =================== SudokuApp ===================
class SudokuApp(ctk.CTk):
    KITTY_IMAGE_FILE = "hello_kitty_sticker.png"
    STICKER_CONFIG = {
        "menu_main": {"size": (200, 200), "fallback_url": "https://i.imgur.com/k9b6m6i.png"},
        "game_main": {"size": (120, 120), "fallback_url": "https://i.imgur.com/k9b6m6i.png"},
    }
    sticker_images = {}

    def __init__(self):
        super().__init__()

        self.title("🎀 Sudoku Hello Kitty VIP Edition 🎀")

        #  Tính toán kích thước dựa trên màn hình
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Xác định kích thước cửa sổ dựa trên màn hình
        if screen_width < 1000 or screen_height < 900:
            # Màn hình nhỏ - sử dụng kích thước nhỏ hơn
            self.window_width = min(800, screen_width - 50)
            self.window_height = min(750, screen_height - 100)
            self.cell_size = max(30, int(self.window_width * 0.045))  # Kích thước ô động
            self.font_size = max(14, int(self.window_width * 0.017))  # Font size động
        else:
            # Màn hình lớn - giữ kích thước gốc
            self.window_width = 800
            self.window_height = 850
            self.cell_size = 45
            self.font_size = 20

        self.geometry(f"{self.window_width}x{self.window_height}")
        self.resizable(True, True)
        
        # Đặt vị trí cửa sổ ở giữa màn hình
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

        self.load_all_stickers()
        self.show_menu()

    # =================== Stickers ===================
    def load_all_stickers(self):
        for name, config in self.STICKER_CONFIG.items():
            image_source = self.KITTY_IMAGE_FILE
            # Điều chỉnh kích thước sticker theo cửa sổ
            size_factor = min(self.window_width / 800, self.window_height / 850)
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

    # =================== Helpers ===================
    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

    def format_time(self, seconds):
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def stop_timer(self):
        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None

    def update_timer(self):
        self.time_elapsed += 1
        self.timer_label.configure(text=self.format_time(self.time_elapsed))
        self.timer_id = self.after(1000, self.update_timer)

    # =================== MENU ===================
    def show_menu(self):
        self.clear_screen()
        self.configure(fg_color=KITTY_BG)
        self.stop_timer()

        
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
            text_color=KITTY_BG, command=self.show_game,
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

    # =================== GAME ===================
    def show_game(self):
        self.clear_screen()
        self.configure(fg_color=KITTY_BG)
        self.stop_timer()
        self.time_elapsed = 0

        self.board = generate_board()
        self.initial_board = [row[:] for row in self.board]
        self.solution = [row[:] for row in self.board]
        solve_board(self.solution)

        header_font_size = max(18, int(self.window_width * 0.03))
        button_font_size = max(14, int(self.window_width * 0.018))

        header_frame = ctk.CTkFrame(self, fg_color=KITTY_ACCENT_PINK, corner_radius=15)
        header_frame.pack(pady=(15, 10), padx=max(20, int(self.window_width * 0.05)), fill='x')
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header_frame, text="Sudoku Challenge",
            font=("Arial Black", header_font_size, "bold"), text_color=KITTY_MAIN_PINK
        ).grid(row=0, column=0, sticky='w', padx=15, pady=8)

        self.timer_label = ctk.CTkLabel(
            header_frame, text=self.format_time(self.time_elapsed),
            font=("Arial Black", header_font_size, "bold"), text_color=KITTY_TEXT
        )
        self.timer_label.grid(row=0, column=1, sticky='e', padx=15, pady=8)
        self.update_timer()

        # Main grid frame
        main_grid_frame = ctk.CTkFrame(self, fg_color=KITTY_BG)
        main_grid_frame.pack(pady=(10, 15), padx=15)
        main_grid_frame.grid_columnconfigure(0, weight=0)
        main_grid_frame.grid_columnconfigure(1, weight=0)

        # Sudoku container
        sudoku_container = ctk.CTkFrame(main_grid_frame, fg_color=KITTY_MAIN_PINK, corner_radius=15)
        sudoku_container.grid(row=0, column=0, padx=(0, 20), sticky="n")

        grid_frame = ctk.CTkFrame(sudoku_container, fg_color=KITTY_BG, corner_radius=10)
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
                else:
                    entry.bind("<KeyRelease>", lambda e, r=i, c=j: self.validate_input(r, c))
                    entry.configure(text_color="#000000")

                row_cells.append(entry)

            row_block_frame.grid(row=i, column=0, columnspan=9, sticky="ew",
                                 pady=(3 if i % 3 == 0 and i != 0 else 1, 1))
            self.cells.append(row_cells)

        # Sticker frame
        game_main_img = self.sticker_images.get("game_main")
        if game_main_img:
            sticker_size = max(100, int(self.window_width * 0.15))
            sticker_frame = ctk.CTkFrame(main_grid_frame, fg_color=KITTY_ACCENT_PINK, 
                                       corner_radius=15, width=sticker_size, height=sticker_size)
            sticker_frame.grid(row=0, column=1, padx=(0, 15), sticky="n", pady=30)
            sticker_frame.grid_propagate(False)

            sticker1 = ctk.CTkLabel(sticker_frame, image=game_main_img, text="", fg_color="transparent")
            sticker1.place(relx=0.5, rely=0.5, anchor="center")

        # Button frame
        btn_frame = ctk.CTkFrame(self, fg_color=KITTY_BG)
        btn_frame.pack(pady=(10, 15))

        controls = [
            ("💡 Hint", self.handle_hint, KITTY_MAIN_PINK),
            ("🔄 Play Again", self.reset_board, KITTY_MAIN_PINK),
            ("👑 Kitty ", self.handle_solve, KITTY_MAIN_PINK),
            ("🏠 Main Menu", self.show_menu, "#CC0000"),
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
        for i in range(9):
            for j in range(9):
                if self.cells[i][j].cget("state") != "disabled" and self.cells[i][j].get() == "":
                    self.cells[i][j].insert(0, str(self.solution[i][j]))
                    if self.is_input_incorrect(i, j, self.solution[i][j]):
                        self.cells[i][j].configure(fg_color="#FFCCCC", text_color=KITTY_ERROR_RED)
                    else:
                        self.cells[i][j].configure(fg_color="#CCFFCC", text_color="#00AA00")
                    self.check_win()
                    return
        messagebox.showinfo("Sudoku", "Tất cả các ô đã được điền! Kiểm tra kết quả.")

    def handle_solve(self):
        response = messagebox.askyesno("Giải Sudoku", "Bạn có chắc chắn muốn xem đáp án? Trò chơi sẽ kết thúc.")
        if response:
            self.stop_timer()
            for i in range(9):
                for j in range(9):
                    self.cells[i][j].configure(state="normal")
                    self.cells[i][j].delete(0, "end")
                    self.cells[i][j].insert(0, str(self.solution[i][j]))
                    self.cells[i][j].configure(state="disabled", fg_color=KITTY_ACCENT_PINK, text_color="#000000")
            messagebox.showinfo("Lời Giải", "Chúc mừng! Đây là lời giải hoàn chỉnh.")

    def validate_input(self, row, col):
        val = self.cells[row][col].get().strip()
        block_color = KITTY_BG if (row // 3 + col // 3) % 2 == 0 else KITTY_BG_ALT

        if not val.isdigit() or not (1 <= int(val) <= 9):
            if val == "":
                self.cells[row][col].configure(fg_color=block_color, text_color="#000000")
                self.check_win()
                return

            self.cells[row][col].delete(0, "end")
            self.cells[row][col].configure(fg_color=KITTY_ERROR_RED, text_color="#CC0000")
            self.after(200, lambda: self.cells[row][col].configure(fg_color=block_color, text_color="#000000"))
            return

        if len(val) > 1:
            val = val[-1]
            self.cells[row][col].delete(0, "end")
            self.cells[row][col].insert(0, val)

        num = int(val)

        if self.is_input_incorrect(row, col, num):
            self.cells[row][col].configure(fg_color="#FFCCCC", text_color=KITTY_ERROR_RED)
            self.check_win()
            return

        if num == self.solution[row][col]:
            self.cells[row][col].configure(fg_color="#CCFFCC", text_color="#00AA00")
        else:
            self.cells[row][col].configure(fg_color="#FFFFAA", text_color="#CC9900")

        self.check_win()

    def check_win(self):
        for i in range(9):
            for j in range(9):
                if self.cells[i][j].cget("state") != "disabled":
                    current_value = self.cells[i][j].get()
                    if current_value == "" or int(current_value) != self.solution[i][j]:
                        return
        self.stop_timer()
        final_time = self.format_time(self.time_elapsed)
        messagebox.showinfo("🎉 Chúc mừng!",
                            f"Bạn đã giải xong Sudoku Hello Kitty VIP Edition 🎀 trong {final_time}! Bạn thật giỏi!")

# =================== Run App ===================
if __name__ == "__main__":
    app = SudokuApp()
    app.mainloop()