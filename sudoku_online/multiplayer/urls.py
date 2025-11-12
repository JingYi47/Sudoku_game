from django.urls import path
from . import views

urlpatterns = [
    path('', views.multiplayer_lobby, name='multiplayer_lobby'),
]
