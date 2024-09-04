from django.urls import path

from .views import LoginView, LogoutView, RegisterView, ActivateUserView

app_name = 'user'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/<int:user_id>/', ActivateUserView.as_view(), name='activate_user'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
