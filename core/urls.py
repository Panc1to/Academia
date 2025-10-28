from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import certificates

urlpatterns = [
    path('registro/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password_reset/', views.password_reset_request, name='password_reset'),
    path('instructor/curso/crear/', views.crear_curso_view, name='crear_curso'),
    path('instructor/curso/<int:pk>/editar/', views.editar_curso_view, name='editar_curso_view'),
    path('instructor/curso/<int:pk>/', views.ver_curso_view, name='ver_curso_view'),
    path('instructor/curso/<int:pk>/eliminar/', views.eliminar_curso_instructor, name='eliminar_curso_instructor'),
    path('instructor/estadisticas/', views.ver_estadisticas_view, name='ver_estadisticas'),
    path('instructor/dashboard/', views.instructor_dashboard, name='instructor_dashboard'),
    path('administracion/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('administracion/usuarios/', views.admin_users, name='admin_users'),
    path('administracion/usuarios/crear/', views.create_user, name='create_user'),
    path('administracion/usuarios/<int:pk>/editar/', views.edit_user, name='edit_user'),
    path('administracion/cursos/', views.admin_courses, name='admin_courses'),
    path('administracion/cursos/crear/', views.create_course, name='create_course'),
    path('administracion/cursos/<int:pk>/editar/', views.edit_course, name='edit_course'),
    path('administracion/cursos/<int:pk>/eliminar/', views.delete_course, name='delete_course'),
    path('administracion/compras/', views.admin_purchases, name='admin_purchases'),
    path('administracion/compras/<int:compra_id>/recibo/', views.download_receipt, name='download_receipt'),
    path('administracion/certificados/', views.admin_certificates, name='admin_certificates'),
    path('administracion/certificados/plantilla/crear/', certificates.create_certificate_template, name='create_certificate_template'),
    path('administracion/certificados/plantilla/<int:pk>/eliminar/', certificates.delete_certificate_template, name='delete_certificate_template'),
    path('', views.home, name='home'),
    path('cursos/', views.course_list, name='course_list'),
    path('cursos/<int:pk>/', views.course_detail, name='course_detail'),
    path('cursos/<int:pk>/pagar/', views.pagar_curso, name='pagar_curso'),
    path('cursos/<int:pk>/contenido/', views.ver_contenido, name='ver_contenido'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
