from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('registro/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password_reset/', views.password_reset_request, name='password_reset'),
    path('instructor/dashboard/', views.instructor_dashboard, name='instructor_dashboard'),
    path('administracion/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('', views.home, name='home'),
    path('cursos/', views.course_list, name='course_list'),
    path('cursos/<int:pk>/', views.course_detail, name='course_detail'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
