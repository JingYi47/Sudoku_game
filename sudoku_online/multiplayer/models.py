from django.db import models
from django.contrib.auth.models import User
import json
import uuid

class MultiplayerRoom(models.Model):
    room_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    player1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='player1_rooms')
    player2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='player2_rooms', null=True, blank=True)
    difficulty = models.CharField(max_length=10, default='Medium')
    board_data = models.TextField()
    solution_data = models.TextField()
    player1_score = models.IntegerField(default=0)
    player2_score = models.IntegerField(default=0)
    player1_progress = models.IntegerField(default=0)
    player2_progress = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='waiting')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def set_board(self, board):
        self.board_data = json.dumps(board)
    
    def get_board(self):
        return json.loads(self.board_data)
    
    def set_solution(self, solution):
        self.solution_data = json.dumps(solution)
    
    def get_solution(self):
        return json.loads(self.solution_data)

class WaitingPlayer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    difficulty = models.CharField(max_length=10)
    joined_at = models.DateTimeField(auto_now_add=True)