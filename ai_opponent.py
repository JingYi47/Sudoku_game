import random
import time

class AIOpponent:
    def __init__(self, difficulty="Medium"):
        self.difficulty = difficulty
        self.speed_settings = {
            "Easy": {"min_delay": 3, "max_delay": 8, "error_chance": 0.3},
            "Medium": {"min_delay": 2, "max_delay": 6, "error_chance": 0.2},
            "Hard": {"min_delay": 1, "max_delay": 4, "error_chance": 0.1},
            "Expert": {"min_delay": 0.5, "max_delay": 2, "error_chance": 0.05}
        }
        self.ai_cells = set()  
        self.correct_moves = 0
        self.wrong_moves = 0
        
    def get_available_cells(self, current_board):
        available = []
        for i in range(9):
            for j in range(9):
                if current_board[i][j] == 0 and (i, j) not in self.ai_cells:
                    available.append((i, j))
        return available
        
    def make_move(self, current_board, solution):
        available_cells = self.get_available_cells(current_board)
        if not available_cells:
            return None, None, None, False
            
        # Chọn ô ngẫu nhiên từ ô trống
        row, col = random.choice(available_cells)
        correct_value = solution[row][col]
        
        # đi sai theo độ khó
        if random.random() < self.speed_settings[self.difficulty]["error_chance"]:
            wrong_values = [num for num in range(1, 10) if num != correct_value]
            if wrong_values:
                value = random.choice(wrong_values)
                is_correct = False
                self.wrong_moves += 1
            else:
                value = correct_value
                is_correct = True
                self.correct_moves += 1
        else:
            value = correct_value
            is_correct = True
            self.correct_moves += 1
            
        # Đánh dấu ô AI đã đi
        self.ai_cells.add((row, col))
        
        return row, col, value, is_correct
    
    def calculate_ai_score(self):
        """Tính điểm AI real-time"""
        base_score = self.correct_moves * 8  # AI điểm thấp hơn người chơi
        penalty = self.wrong_moves * 5
        return max(0, base_score - penalty)
    
    def get_progress(self, total_empty):
        """Tính % tiến độ của AI"""
        return (len(self.ai_cells) / total_empty) * 100 if total_empty > 0 else 0
    
    def reset_ai(self):
        """Reset trạng thái AI"""
        self.ai_cells.clear()
        self.correct_moves = 0
        self.wrong_moves = 0