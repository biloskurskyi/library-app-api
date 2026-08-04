from django.urls import path

from . import views

urlpatterns = [
    path('loans/', views.LoanListView.as_view()),
    path('loans/<int:pk>/returned/', views.ReturnedLoanView.as_view()),
]
