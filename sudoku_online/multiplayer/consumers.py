import json
import random
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import MultiplayerRoom, WaitingPlayer

def generate_sudoku_board(difficulty):
    """Tạo Sudoku board thật tùy theo độ khó"""
    base = [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9]
    ]
    
    # Tùy chỉnh theo độ khó
    if difficulty == 'Easy':
        cells_to_remove = 10
    elif difficulty == 'Medium':
        cells_to_remove = 25
    else:  # Hard
        cells_to_remove = 40
    
    # Tạo bản sao và xóa ngẫu nhiên
    board = [row[:] for row in base]
    removed = 0
    while removed < cells_to_remove:
        row, col = random.randint(0, 8), random.randint(0, 8)
        if board[row][col] != 0:
            board[row][col] = 0
            removed += 1
    
    return board

def generate_solution(board):
    """Tạo solution - tạm thời trả về board đầy đủ"""
    solution = [
        [5, 3, 4, 6, 7, 8, 9, 1, 2],
        [6, 7, 2, 1, 9, 5, 3, 4, 8],
        [1, 9, 8, 3, 4, 2, 5, 6, 7],
        [8, 5, 9, 7, 6, 1, 4, 2, 3],
        [4, 2, 6, 8, 5, 3, 7, 9, 1],
        [7, 1, 3, 9, 2, 4, 8, 5, 6],
        [9, 6, 1, 5, 3, 7, 2, 8, 4],
        [2, 8, 7, 4, 1, 9, 6, 3, 5],
        [3, 4, 5, 2, 8, 6, 1, 7, 9]
    ]
    return solution

class MultiplayerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
            return
        
        self.room_group_name = None
        await self.accept()

    async def disconnect(self, close_code):
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        await self.remove_from_waiting()

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data['type']
        
        if message_type == 'join_matchmaking':
            await self.join_matchmaking(data)
        elif message_type == 'update_progress':
            await self.update_progress(data)
        elif message_type == 'make_move':
            await self.make_move(data)

    async def join_matchmaking(self, data):
        difficulty = data.get('difficulty', 'Medium')
        
        opponent = await self.find_opponent(difficulty)
        
        if opponent:
            room = await self.create_room(self.user, opponent, difficulty)
            self.room_group_name = f"room_{room.room_id}"
            
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            # Gửi board thật cho cả 2 người chơi
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'match_found',
                    'room_id': str(room.room_id),
                    'player1': self.user.username,
                    'player2': opponent.username,
                    'difficulty': difficulty,
                    'board': room.get_board()  # GỬI BOARD THẬT
                }
            )
        else:
            await self.add_to_waiting(difficulty)
            await self.send(text_data=json.dumps({
                'type': 'waiting',
                'message': 'Finding opponent...'
            }))

    async def match_found(self, event):
        await self.send(text_data=json.dumps({
            'type': 'match_found',
            'room_id': event['room_id'],
            'player1': event['player1'],
            'player2': event['player2'],
            'difficulty': event['difficulty'],
            'board': event['board']  # GỬI BOARD CHO CLIENT
        }))

    async def update_progress(self, data):
        if not self.room_group_name:
            return
            
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'opponent_update',
                'username': self.user.username,
                'score': data['score'],
                'progress': data['progress']
            }
        )

    async def opponent_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'opponent_update',
            'username': event['username'],
            'score': event['score'],
            'progress': event['progress']
        }))

    async def make_move(self, data):
        """Xử lý khi người chơi đi nước đi"""
        if not self.room_group_name:
            return
            
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'opponent_move',
                'username': self.user.username,
                'row': data['row'],
                'col': data['col'],
                'value': data['value']
            }
        )

    async def opponent_move(self, event):
        """Nhận nước đi từ đối thủ"""
        await self.send(text_data=json.dumps({
            'type': 'opponent_move',
            'username': event['username'],
            'row': event['row'],
            'col': event['col'],
            'value': event['value']
        }))

    # Database operations
    @database_sync_to_async
    def find_opponent(self, difficulty):
        try:
            waiting_player = WaitingPlayer.objects.filter(
                difficulty=difficulty
            ).exclude(user=self.user).first()
            
            if waiting_player:
                opponent = waiting_player.user
                waiting_player.delete()
                return opponent
            return None
        except Exception:
            return None

    @database_sync_to_async
    def add_to_waiting(self, difficulty):
        WaitingPlayer.objects.update_or_create(
            user=self.user,
            defaults={'difficulty': difficulty}
        )

    @database_sync_to_async
    def remove_from_waiting(self):
        WaitingPlayer.objects.filter(user=self.user).delete()

    @database_sync_to_async
    def create_room(self, player1, player2, difficulty):
        # TẠO BOARD THẬT
        board = generate_sudoku_board(difficulty)
        solution = generate_solution(board)
        
        room = MultiplayerRoom.objects.create(
            player1=player1,
            player2=player2,
            difficulty=difficulty
        )
        room.set_board(board)
        room.set_solution(solution)
        room.status = 'active'
        room.save()
        
        return room