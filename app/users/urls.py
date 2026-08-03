from django.urls import path
from rest_framework_simplejwt.views import TokenBlacklistView

from . import views

urlpatterns = [
    path('users/', views.UserListView.as_view()),
    path('users/<int:pk>/', views.UserDetailView.as_view()),
    path('activate/<str:token>/', views.ActivationView.as_view()),
    path('login/', views.LoginView.as_view()),
    path('logout/', TokenBlacklistView.as_view()),
]
