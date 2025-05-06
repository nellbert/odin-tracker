from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    # Route for marking a lesson complete
    path('complete/<int:lesson_id>/', views.mark_complete, name='mark_complete'),
    path('uncomplete/<int:lesson_id>/', views.unmark_complete, name='unmark_complete'),
    path('signup/', views.signup, name='signup'),
    path('settings/', views.user_settings, name='user_settings'),
    path('settings/reset/', views.reset_progress, name='reset_progress'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('achievements/', views.achievements_page, name='achievements_list'),
    # Optional: Redirect root to dashboard if needed later, or handle in project urls
    # path('', views.dashboard, name='home'), # Example if dashboard is the main page
] 