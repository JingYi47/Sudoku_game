from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.shortcuts import redirect

# THÊM hàm redirect trang chủ
def home_redirect(request):
    return HttpResponse('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sudoku Multiplayer</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    max-width: 800px; 
                    margin: 100px auto; 
                    padding: 20px; 
                    text-align: center;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                .container {
                    background: rgba(255,255,255,0.1);
                    padding: 40px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                }
                h1 { font-size: 3em; margin-bottom: 20px; }
                .btn {
                    display: inline-block;
                    padding: 15px 30px;
                    background: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    font-size: 1.2em;
                    margin: 10px;
                    transition: transform 0.3s;
                }
                .btn:hover {
                    transform: scale(1.05);
                    background: #45a049;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎮 Sudoku Multiplayer</h1>
                <p style="font-size: 1.2em; margin-bottom: 30px;">
                    Battle against other players in real-time Sudoku matches!
                </p>
                <a href="/multiplayer/" class="btn">🚀 Play Multiplayer</a>
                <a href="/admin/" class="btn" style="background: #2196F3;">⚙️ Admin Panel</a>
                
                <div style="margin-top: 40px;">
                    <h3>Features:</h3>
                    <p>✅ Real-time multiplayer battles</p>
                    <p>✅ Live score tracking</p>
                    <p>✅ Multiple difficulty levels</p>
                    <p>✅ Matchmaking system</p>
                </div>
            </div>
        </body>
        </html>
    ''')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('multiplayer/', include('multiplayer.urls')),
    path('', home_redirect),  # TRANG CHỦ - THÊM DÒNG NÀY
]