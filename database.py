import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="sudoku_game.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Bảng người dùng
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_login TEXT
            )
        ''')
        
        # Bảng thống kê người chơi
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                level TEXT NOT NULL,
                total_score INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                games_won INTEGER DEFAULT 0,
                best_time INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, level)
            )
        ''')
        
        # Bảng lịch sử game
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                level TEXT NOT NULL,
                score INTEGER DEFAULT 0,
                time_taken INTEGER DEFAULT 0,
                date_played TEXT NOT NULL,
                game_mode TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def register_user(self, username, password):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (username, password, created_at)
                VALUES (?, ?, ?)
            ''', (username, password, datetime.now().isoformat()))
            
            user_id = cursor.lastrowid
            
            # Khởi tạo stats cho các level
            levels = ['Easy', 'Medium', 'Hard', 'Expert']
            for level in levels:
                cursor.execute('''
                    INSERT INTO user_stats (user_id, level)
                    VALUES (?, ?)
                ''', (user_id, level))
            
            conn.commit()
            return True, "Đăng ký thành công!"
        except sqlite3.IntegrityError:
            return False, "Tên người dùng đã tồn tại!"
        finally:
            conn.close()
    
    def login_user(self, username, password):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, password FROM users WHERE username = ?
        ''', (username,))
        
        result = cursor.fetchone()
        if result and result[1] == password:
            # Cập nhật last_login
            cursor.execute('''
                UPDATE users SET last_login = ? WHERE id = ?
            ''', (datetime.now().isoformat(), result[0]))
            conn.commit()
            conn.close()
            return True, result[0]  # Trả về user_id
        else:
            conn.close()
            return False, "Sai tên đăng nhập hoặc mật khẩu!"
    
    def update_user_stats(self, user_id, level, score, time_taken, won=False):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Cập nhật stats
        cursor.execute('''
            UPDATE user_stats 
            SET total_score = total_score + ?,
                games_played = games_played + 1,
                games_won = games_won + ?,
                best_time = CASE 
                    WHEN ? < best_time OR best_time = 0 THEN ? 
                    ELSE best_time 
                END
            WHERE user_id = ? AND level = ?
        ''', (score, int(won), time_taken, time_taken, user_id, level))
        
        # Lưu lịch sử game
        cursor.execute('''
            INSERT INTO game_history (user_id, level, score, time_taken, date_played, game_mode)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, level, score, time_taken, datetime.now().isoformat(), 'single'))
        
        conn.commit()
        conn.close()
    
    def get_leaderboard(self, level=None, limit=10):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if level:
            cursor.execute('''
                SELECT u.username, us.total_score, us.games_played, us.games_won
                FROM user_stats us
                JOIN users u ON us.user_id = u.id
                WHERE us.level = ?
                ORDER BY us.total_score DESC
                LIMIT ?
            ''', (level, limit))
        else:
            cursor.execute('''
                SELECT u.username, 
                       SUM(us.total_score) as total_score,
                       SUM(us.games_played) as games_played,
                       SUM(us.games_won) as games_won
                FROM user_stats us
                JOIN users u ON us.user_id = u.id
                GROUP BY u.id, u.username
                ORDER BY total_score DESC
                LIMIT ?
            ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        leaderboard = []
        for i, (username, score, played, won) in enumerate(results):
            win_rate = (won / played * 100) if played > 0 else 0
            leaderboard.append({
                'rank': i + 1,
                'username': username,
                'score': score,
                'games_played': played,
                'win_rate': round(win_rate, 1)
            })
        
        return leaderboard
    
    def get_user_stats(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT level, total_score, games_played, games_won, best_time
            FROM user_stats 
            WHERE user_id = ?
        ''', (user_id,))
        
        stats = cursor.fetchall()
        conn.close()
        
        return stats