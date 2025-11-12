from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def multiplayer_lobby(request):
    return render(request, 'multiplayer.html')