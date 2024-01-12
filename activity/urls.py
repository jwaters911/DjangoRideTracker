# activity/urls.py
from django.urls import path
from django.contrib.auth.views import LoginView
from .views import activity_list, activity_details, index, update_summary, delete_activity, delete_comment
from . import views


urlpatterns = [

    path('activity_list/', activity_list, name='activity_list'),
    path('activity/<int:activity_id>/', activity_details, name='activity_details'),
    path('activity/<int:activity_id>/add_comment/', views.add_comment, name='add_comment'),
    path('activity/<int:activity_id>/fetch_comments/', views.fetch_comments, name='fetch_comments'),
    path('activity/<int:activity_id>/edit_comment/<int:comment_id>/', views.edit_comment, name='edit_comment'),
    path('delete_comment/<int:comment_id>/', delete_comment, name='delete_comment'),
    path('activity/update_summary/', update_summary, name='update_summary'),
    path('activity/<int:activity_id>/delete/', delete_activity, name='delete_activity'),
    path('', index, name='index'),

    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register")
]