from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.db import models
from typing import Optional, cast
from .models import Curso, Compra, Usuario, Certificado
from .forms import EstudianteRegistrationForm, InstructorCreationForm, CourseForm, AdminUserCreationForm

def home(request: HttpRequest) -> HttpResponse:
	"""Página de inicio simple.

	Renderiza una plantilla básica para verificar que las vistas funcionan.
	"""
	return render(request, "core/index.html", {"title": "Conecta Saber"})

def course_list(request: HttpRequest) -> HttpResponse:
    """Muestra una lista de todos los cursos disponibles."""
    courses = Curso.objects.all()
    return render(request, "core/course_list.html", {"courses": courses})

def course_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Muestra los detalles de un curso específico y sus módulos."""
    course = get_object_or_404(Curso, pk=pk)
    return render(request, "core/course_detail.html", {"course": course})

def login_view(request: HttpRequest) -> HttpResponse:
    """Vista para el inicio de sesión de usuarios."""
    # Si el usuario ya está autenticado, redirigir según su tipo
    if request.user.is_authenticated:
        usuario = cast(Usuario, request.user)
        if usuario.is_superuser:
            return redirect('admin_dashboard')
        elif usuario.es_instructor:
            return redirect('instructor_dashboard')
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember_me') == 'on'
        
        if not username or not password:
            messages.error(request, 'Por favor, completa todos los campos.')
            return render(request, 'core/login.html')

        try:
            # Intentar encontrar usuario por email
            if '@' in username:
                try:
                    user_obj = Usuario.objects.get(email=username)
                    username = user_obj.username
                except Usuario.DoesNotExist:
                    user_obj = None
            
            # Autenticar usuario
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    # Iniciar sesión y hacer cast al modelo Usuario
                    login(request, user)
                    usuario = cast(Usuario, user)
                    
                    # Configurar la duración de la sesión
                    if not remember_me:
                        request.session.set_expiry(0)  # La sesión expira al cerrar el navegador
                    else:
                        # Sesión dura 30 días
                        request.session.set_expiry(30 * 24 * 60 * 60)
                    
                    # Personalizar mensaje según el tipo de usuario
                    if usuario.es_estudiante:
                        messages.success(request, f'¡Bienvenido de vuelta a tus cursos, {usuario.nombre_completo}!')
                    elif usuario.es_instructor:
                        messages.success(request, f'¡Bienvenido, profesor {usuario.nombre_completo}!')
                    else:
                        messages.success(request, f'¡Bienvenido, {usuario.nombre_completo}!')
                    
                    # Redirigir según el tipo de usuario
                    if usuario.is_superuser:
                        return redirect('admin_dashboard')
                    elif usuario.es_instructor:
                        return redirect('instructor_dashboard')
                    return redirect('dashboard')
                else:
                    messages.warning(request, 'Tu cuenta está desactivada. Por favor, contacta con soporte.')
            else:
                messages.error(request, 'Los datos ingresados no son correctos. Por favor, verifica e intenta nuevamente.')
        
        except Exception as e:
            messages.error(request, 'Ha ocurrido un error. Por favor, intenta más tarde.')
            print(f"Error en login: {str(e)}")  # Para debugging
    
    # Para peticiones GET o si hay errores
    return render(request, 'core/login.html', {
        'next': request.GET.get('next', '')
    })

def logout_view(request: HttpRequest) -> HttpResponse:
    """Vista para cerrar sesión."""
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('home')

def password_reset_request(request: HttpRequest) -> HttpResponse:
    """Vista para solicitar restablecimiento de contraseña."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if not email:
            messages.error(request, 'Por favor, ingresa un correo electrónico.')
            return render(request, 'core/password_reset.html')

        try:
            user = Usuario.objects.get(email=email)
            if not user.is_active:
                messages.error(request, 'Esta cuenta está desactivada.')
                return render(request, 'core/password_reset.html')

            # Generamos el token
            subject = "Solicitud de restablecimiento de contraseña"
            context = {
                'user': user,
                'domain': request.get_host(),
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
                'protocol': 'https' if request.is_secure() else 'http'
            }
            
            try:
                # Renderizamos el email
                email_content = render_to_string("registration/password_reset_email.html", context)
                
                # Enviamos el correo
                send_mail(
                    subject=subject,
                    message=email_content,
                    from_email=None,  # Usará el DEFAULT_FROM_EMAIL de settings
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                
                messages.success(request, 'Se ha enviado un correo con instrucciones para restablecer tu contraseña.')
                return redirect('login')
                
            except (BadHeaderError, Exception) as e:
                messages.error(request, 'Error al enviar el correo. Por favor, intenta más tarde.')
                
        except Usuario.DoesNotExist:
            # Por seguridad, no revelamos si el email existe o no
            messages.success(request, 'Si existe una cuenta con ese correo, recibirás las instrucciones para restablecer tu contraseña.')
    
    return render(request, 'core/password_reset.html')

@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """Muestra el panel de control del usuario con sus cursos y progreso."""
    usuario = cast(Usuario, request.user)
    if usuario.es_instructor:
        return redirect('instructor_dashboard')
        
    compras = Compra.objects.filter(estudiante=usuario, estado_pago='validado')
    cursos_comprados = [compra.curso for compra in compras]
    return render(request, "core/dashboard.html", {"cursos": cursos_comprados})

@login_required
def instructor_dashboard(request: HttpRequest) -> HttpResponse:
    """Muestra el panel de control para instructores."""
    usuario = cast(Usuario, request.user)
    if not usuario.es_instructor:
        messages.error(request, 'No tienes permisos para acceder al panel de instructor.')
        return redirect('dashboard')
        
    # Obtener los cursos del instructor
    cursos = Curso.objects.filter(instructor=usuario).order_by('-fecha_creacion')
    
    # Calcular estadísticas
    cursos_count = cursos.count()
    estudiantes_count = Compra.objects.filter(
        curso__instructor=usuario,
        estado_pago='validado'
    ).values('estudiante').distinct().count()
    
    # Calcular ingresos totales
    total_ingresos = Compra.objects.filter(
        curso__instructor=usuario,
        estado_pago='validado'
    ).aggregate(total=models.Sum('monto_pagado'))['total'] or 0
    
    context = {
        'cursos': cursos,
        'cursos_count': cursos_count,
        'estudiantes_count': estudiantes_count,
        'total_ingresos': f"${total_ingresos:,.2f}"
    }
    
    return render(request, "core/instructor_dashboard.html", context)

def register(request: HttpRequest) -> HttpResponse:
    """Vista para el registro de nuevos estudiantes."""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = EstudianteRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                '¡Registro exitoso! Por favor, inicia sesión con tus nuevas credenciales.'
            )
            return redirect('login')
    else:
        form = EstudianteRegistrationForm()
    return render(request, 'core/register.html', {'form': form})

@login_required
def admin_dashboard(request: HttpRequest) -> HttpResponse:
    """Muestra el panel de control para administradores."""
    usuario = cast(Usuario, request.user)
    # Verificar si el usuario es administrador
    if not usuario.is_superuser:
        messages.error(request, 'No tienes permisos para acceder al panel de administración.')
        return redirect('home')
        
    # Obtener estadísticas generales
    total_usuarios = Usuario.objects.count()
    total_instructores = Usuario.objects.filter(es_instructor=True).count()
    total_estudiantes = Usuario.objects.filter(es_estudiante=True).count()
    total_cursos = Curso.objects.count()
    total_compras = Compra.objects.filter(estado_pago='validado').count()
    
    # Calcular ingresos totales
    total_ingresos = Compra.objects.filter(
        estado_pago='validado'
    ).aggregate(total=models.Sum('monto_pagado'))['total'] or 0

    context = {
        'total_usuarios': total_usuarios,
        'total_instructores': total_instructores,
        'total_estudiantes': total_estudiantes,
        'total_cursos': total_cursos,
        'total_compras': total_compras,
        'total_ingresos': f"${total_ingresos:,.2f}",
    }
    
    return render(request, 'core/admin/dashboard.html', context)

@login_required
def admin_users(request: HttpRequest) -> HttpResponse:
    """Vista para la gestión de usuarios."""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('home')
    
    usuarios = Usuario.objects.all().order_by('date_joined')
    estudiantes = usuarios.filter(es_estudiante=True)
    instructores = usuarios.filter(es_instructor=True)
    administradores = usuarios.filter(is_superuser=True)
    
    context = {
        'usuarios': usuarios,
        'total_usuarios': usuarios.count(),
        'total_estudiantes': estudiantes.count(),
        'total_instructores': instructores.count(),
        'total_administradores': administradores.count(),
        'estudiantes': estudiantes,
        'instructores': instructores,
        'administradores': administradores,
    }
    
    return render(request, 'core/admin/users.html', context)

@login_required
def create_user(request: HttpRequest) -> HttpResponse:
    """Vista para crear un nuevo usuario desde el panel de administración."""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para crear usuarios.')
        return redirect('admin_users')
        
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f'Usuario {user.username} creado exitosamente como {form.cleaned_data["tipo_usuario"]}.'
            )
            return redirect('admin_users')
    else:
        form = AdminUserCreationForm()
    
    return render(request, 'core/admin/create_user.html', {'form': form})

@login_required
def admin_courses(request: HttpRequest) -> HttpResponse:
    """Vista para la gestión de cursos."""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('home')
    
    cursos = Curso.objects.all().order_by('-fecha_creacion')
    total_estudiantes = Compra.objects.filter(estado_pago='validado').values('estudiante').distinct().count()
    total_certificados = Certificado.objects.count()
    
    context = {
        'cursos': cursos,
        'total_cursos': cursos.count(),
        'total_estudiantes_inscritos': total_estudiantes,
        'total_certificados': total_certificados,
    }
    
    return render(request, 'core/admin/courses.html', context)

@login_required
def edit_course(request: HttpRequest, pk: int) -> HttpResponse:
    """Vista para editar un curso existente."""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para editar cursos.')
        return redirect('admin_courses')
        
    curso = get_object_or_404(Curso, pk=pk)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=curso)
        if form.is_valid():
            form.save()
            messages.success(request, 'Curso actualizado exitosamente.')
            return redirect('admin_courses')
    else:
        form = CourseForm(instance=curso)
    
    return render(request, 'core/admin/edit_course.html', {
        'form': form,
        'curso': curso
    })

@login_required
def delete_course(request: HttpRequest, pk: int) -> HttpResponse:
    """Vista para eliminar un curso."""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para eliminar cursos.')
        return redirect('admin_courses')
        
    curso = get_object_or_404(Curso, pk=pk)
    
    if request.method == 'POST':
        curso.delete()
        messages.success(request, 'Curso eliminado exitosamente.')
        return redirect('admin_courses')
    
    return render(request, 'core/admin/delete_course.html', {'curso': curso})

@login_required
def admin_purchases(request: HttpRequest) -> HttpResponse:
    """Vista para la gestión de compras."""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('home')
    
    compras = Compra.objects.all().order_by('-fecha_compra')
    total_ingresos = compras.filter(estado_pago='validado').aggregate(
        total=models.Sum('monto_pagado')
    )['total'] or 0
    
    context = {
        'compras': compras,
        'total_compras': compras.count(),
        'compras_validadas': compras.filter(estado_pago='validado').count(),
        'compras_pendientes': compras.filter(estado_pago='pendiente').count(),
        'total_ingresos': f"${total_ingresos:,.2f}",
    }
    
    return render(request, 'core/admin/purchases.html', context)

@login_required
def admin_certificates(request: HttpRequest) -> HttpResponse:
    """Vista para la gestión de certificados."""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('home')
    
    certificados = Certificado.objects.all().order_by('-fecha_emision')
    
    context = {
        'certificados': certificados,
        'total_certificados': certificados.count(),
    }
    
    return render(request, 'core/admin/certificates.html', context)

@login_required
def create_course(request: HttpRequest) -> HttpResponse:
    """Vista para crear un nuevo curso."""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para crear cursos.')
        return redirect('admin_courses')
        
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            curso = form.save(commit=False)
            curso.instructor = request.user
            curso.save()
            messages.success(request, 'Curso creado exitosamente.')
            return redirect('admin_courses')
    else:
        form = CourseForm()
    
    return render(request, 'core/admin/create_course.html', {'form': form})
    if request.method == 'POST':
        form = InstructorCreationForm(request.POST)
        if form.is_valid():
            instructor = form.save()
            messages.success(
                request,
                f'Instructor creado exitosamente. Usuario: {instructor.username}, Contraseña: {request.POST["password1"]}'
            )
            return redirect('admin_dashboard')
    else:
        form = InstructorCreationForm()

    # Obtener estadísticas
    total_usuarios = Usuario.objects.count()
    total_instructores = Usuario.objects.filter(es_instructor=True).count()
    total_estudiantes = Usuario.objects.filter(es_estudiante=True).count()
    total_cursos = Curso.objects.count()
    total_compras = Compra.objects.filter(estado_pago='validado').count()
    
    # Calcular ingresos totales
    total_ingresos = Compra.objects.filter(
        estado_pago='validado'
    ).aggregate(total=models.Sum('monto_pagado'))['total'] or 0
    
    context = {
        'total_usuarios': total_usuarios,
        'total_instructores': total_instructores,
        'total_estudiantes': total_estudiantes,
        'total_cursos': total_cursos,
        'total_compras': total_compras,
        'total_ingresos': f"${total_ingresos:,.2f}",
        'form': form
    }
    
    return render(request, 'core/admin_dashboard.html', context)
