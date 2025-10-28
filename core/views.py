from typing import Optional, cast
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.tokens import default_token_generator
from django import forms
from django.contrib import messages
from django.core.mail import send_mail, BadHeaderError
from django.db.models import Sum
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from .models import Curso, Compra, Usuario, Certificado
from .forms import EstudianteRegistrationForm, InstructorCreationForm, CourseForm, AdminUserCreationForm
from .utils import generate_purchase_receipt

def home(request: HttpRequest) -> HttpResponse:
	"""Página de inicio simple.

	Renderiza una plantilla básica para verificar que las vistas funcionan.
	"""
	return render(request, "core/index.html", {"title": "Conecta Saber"})

def course_list(request: HttpRequest) -> HttpResponse:
    """Muestra una lista de todos los cursos disponibles."""
    # Obtener todos los cursos activos
    courses = Curso.objects.all()
    user_courses = []
    
    if request.user.is_authenticated:
        usuario = cast(Usuario, request.user)
        if usuario.es_estudiante:
            # Obtener los cursos que el estudiante ya ha comprado
            compras = Compra.objects.filter(
                estudiante=usuario,
                estado_pago='validado'
            ).values_list('curso_id', flat=True)
            user_courses = Curso.objects.filter(id__in=compras)
    
    context = {
        "courses": courses,
        "user_courses": user_courses,
    }
    
    return render(request, "core/course_list.html", context)

@login_required
def pagar_curso(request: HttpRequest, pk: int) -> HttpResponse:
    """Vista para procesar el pago de un curso."""
    curso = get_object_or_404(Curso, pk=pk, estado='activo')
    usuario = cast(Usuario, request.user)
    
    # Verificar si el usuario ya compró el curso
    if Compra.objects.filter(estudiante=usuario, curso=curso, estado_pago='validado').exists():
        messages.info(request, 'Ya tienes acceso a este curso.')
        return redirect('ver_contenido', pk=curso.pk)
    
    if request.method == 'POST':
        # Simular validación del pago
        try:
            # Crear registro de compra
            Compra.objects.create(
                estudiante=usuario,
                curso=curso,
                monto_pagado=curso.precio,
                estado_pago='validado'
            )
            messages.success(request, '¡Pago exitoso! Ahora tienes acceso al curso.')
            return redirect('ver_contenido', pk=curso.pk)
        except Exception as e:
            messages.error(request, 'Ha ocurrido un error procesando el pago. Por favor, intenta nuevamente.')
            print(f"Error en pago: {str(e)}")
    
    return render(request, 'core/pago_curso.html', {'curso': curso})

@login_required
def ver_contenido(request: HttpRequest, pk: int) -> HttpResponse:
    """Vista para ver el contenido de un curso comprado."""
    curso = get_object_or_404(Curso, pk=pk)
    usuario = cast(Usuario, request.user)
    
    # Verificar si el usuario tiene acceso al curso
    if not Compra.objects.filter(estudiante=usuario, curso=curso, estado_pago='validado').exists():
        messages.error(request, 'No tienes acceso a este curso. Por favor, realiza la compra primero.')
        return redirect('course_list')
    
    return render(request, 'core/contenido_curso.html', {'curso': curso})

def course_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Muestra los detalles de un curso específico y sus módulos."""
    course = get_object_or_404(Curso, pk=pk)
    return render(request, "core/course_detail.html", {"course": course})

def login_view(request: HttpRequest) -> HttpResponse:
    """Vista para el inicio de sesión de usuarios."""
    # Limpiar mensajes pendientes al mostrar el formulario de login
    if request.method == 'GET':
        list(messages.get_messages(request))
    
    # Verificar si el usuario ya está autenticado
    if request.user.is_authenticated:
        # Obtener el usuario actual y convertirlo a nuestro modelo Usuario
        usuario = cast(Usuario, request.user)
        
        # Redirigir según el tipo de usuario
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
                    
                    # Redirigir directamente sin mensajes de bienvenida
                    
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
    # Limpiamos la sesión y hacemos logout
    logout(request)
    request.session.flush()
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
    
    context = {
        'cursos': cursos,
        'cursos_count': cursos_count,
        'estudiantes_count': estudiantes_count
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
    ).aggregate(total=Sum('monto_pagado'))['total'] or 0

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
    
    # Limpiar mensajes pendientes de otras secciones
    list(messages.get_messages(request))
    
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
def edit_user(request: HttpRequest, pk: int) -> HttpResponse:
    """Vista para editar un usuario existente desde el panel de administración."""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para editar usuarios.')
        return redirect('admin_users')
        
    usuario = get_object_or_404(Usuario, pk=pk)
    
    if request.method == 'POST':
        # Obtener los datos del formulario
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        nombre_completo = request.POST.get('nombre_completo', '').strip()
        tipo_usuario = request.POST.get('tipo_usuario')
        titulo_especialidad = request.POST.get('titulo_especialidad', '').strip()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Validar que el username no esté tomado por otro usuario
        if username != usuario.username:
            if Usuario.objects.filter(username=username).exists():
                messages.error(request, 'Ya existe un usuario con ese nombre de usuario.')
                return render(request, 'core/admin/edit_user.html', {
                    'form': AdminUserCreationForm(instance=usuario),
                    'usuario': usuario
                })
        
        # Validar que el email no esté tomado por otro usuario
        if email != usuario.email:
            if Usuario.objects.filter(email=email).exists():
                messages.error(request, 'Ya existe un usuario con ese correo electrónico.')
                return render(request, 'core/admin/edit_user.html', {
                    'form': AdminUserCreationForm(instance=usuario),
                    'usuario': usuario
                })
        
        # Validar contraseñas si se proporcionan
        if password1 or password2:
            if password1 != password2:
                messages.error(request, 'Las contraseñas no coinciden.')
                return render(request, 'core/admin/edit_user.html', {
                    'form': AdminUserCreationForm(instance=usuario),
                    'usuario': usuario
                })
        
        # Actualizar el usuario
        usuario.username = username
        usuario.email = email
        usuario.nombre_completo = nombre_completo
        
        # Actualizar contraseña si se proporcionó
        if password1:
            usuario.set_password(password1)
        
        # Actualizar tipo de usuario
        usuario.es_estudiante = tipo_usuario == 'estudiante'
        usuario.es_instructor = tipo_usuario == 'instructor'
        usuario.is_superuser = tipo_usuario == 'admin'
        usuario.is_staff = tipo_usuario == 'admin'
        
        # Actualizar título/especialidad para instructores
        if tipo_usuario == 'instructor':
            usuario.titulo_especialidad = titulo_especialidad
        
        usuario.save()
        
        return redirect('admin_users')
    else:
        # Pre-seleccionar el tipo de usuario actual
        initial_tipo = 'estudiante'
        if usuario.es_instructor:
            initial_tipo = 'instructor'
        elif usuario.is_superuser:
            initial_tipo = 'admin'
            
        form = AdminUserCreationForm(instance=usuario, initial={'tipo_usuario': initial_tipo})
        # Hacer los campos de contraseña opcionales
        form.fields['password1'].required = False
        form.fields['password2'].required = False
        
        # Ocultar el campo de título/especialidad si no es instructor
        if not usuario.es_instructor:
            form.fields['titulo_especialidad'].widget = forms.HiddenInput()
    
    return render(request, 'core/admin/edit_user.html', {
        'form': form,
        'usuario': usuario
    })

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

from django.http import FileResponse
from .utils import generate_purchase_receipt
from django.db.models import Sum
from typing import cast

@login_required
def admin_purchases(request: HttpRequest) -> HttpResponse:
    """Vista para la gestión de compras."""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('home')
    
    compras = Compra.objects.all().order_by('-fecha_compra')
    # Calcular sólo las compras validadas (ventas reales)
    total_ingresos = Compra.objects.filter(estado_pago='validado').aggregate(
        total=Sum('monto_pagado')
    )['total'] or 0

    context = {
        'compras': compras,
        'total_compras': compras.count(),
        # Pasamos el número bruto y dejamos el formato para la plantilla
        'total_ingresos': total_ingresos,
    }

    return render(request, 'core/admin/purchases.html', context)

@login_required
def download_receipt(request: HttpRequest, compra_id: int) -> HttpResponse:
    """Vista para descargar el comprobante de compra."""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para descargar comprobantes.')
        return redirect('home')
    
    compra = get_object_or_404(Compra, pk=compra_id)
    pdf = generate_purchase_receipt(compra)
    
    # Crear la respuesta HTTP con el PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="comprobante_compra_{compra_id}.pdf"'
    return response
    

@login_required
def admin_certificates(request: HttpRequest) -> HttpResponse:
    """Vista para la gestión de certificados."""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('home')
    
    from .models import PlantillaCertificado
    from django.utils import timezone
    from datetime import timedelta
    
    # Obtener certificados y plantillas
    certificados = Certificado.objects.all().order_by('-fecha_emision')
    plantillas = PlantillaCertificado.objects.all().order_by('-fecha_creacion')
    
    # Calcular certificados de este mes
    hoy = timezone.now()
    inicio_mes = hoy.replace(day=1)
    certificados_mes = Certificado.objects.filter(
        fecha_emision__gte=inicio_mes
    ).count()
    
    context = {
        'certificados': certificados,
        'plantillas': plantillas,
        'total_certificados': certificados.count(),
        'total_plantillas': plantillas.count(),
        'certificados_mes': certificados_mes,
    }
    
    return render(request, 'core/admin/certificates.html', context)

@login_required
def crear_curso_view(request: HttpRequest) -> HttpResponse:
    """Vista para crear un nuevo curso como instructor."""
    usuario = cast(Usuario, request.user)
    if not usuario.es_instructor:
        messages.error(request, 'No tienes permisos para crear cursos.')
        return redirect('home')
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            curso = form.save(commit=False)
            curso.instructor = request.user
            curso.save()
            messages.success(request, 'Curso creado exitosamente.')
            return redirect('instructor_dashboard')
    else:
        # Crear formulario con el instructor pre-seleccionado
        form = CourseForm(initial={'instructor': request.user})
        # Ocultar el campo instructor
        form.fields['instructor'].widget = forms.HiddenInput()
        form.fields['instructor'].required = False
    
    return render(request, 'core/instructor/crear_curso.html', {'form': form})

@login_required
def editar_curso_view(request: HttpRequest, pk: int) -> HttpResponse:
    """Vista para editar un curso existente como instructor."""
    usuario = cast(Usuario, request.user)
    if not usuario.es_instructor:
        messages.error(request, 'No tienes permisos para editar cursos.')
        return redirect('home')
        
    curso = get_object_or_404(Curso, pk=pk, instructor=request.user)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=curso)
        if form.is_valid():
            form.save()
            messages.success(request, 'Curso actualizado exitosamente.')
            return redirect('instructor_dashboard')
    else:
        form = CourseForm(instance=curso)
        # Ocultar el campo instructor para que no pueda cambiarlo
        form.fields['instructor'].widget = forms.HiddenInput()
        form.fields['instructor'].required = False
    
    return render(request, 'core/instructor/editar_curso.html', {
        'form': form,
        'curso': curso
    })

@login_required
def ver_curso_view(request: HttpRequest, pk: int) -> HttpResponse:
    """Vista para ver los detalles de un curso como instructor."""
    usuario = cast(Usuario, request.user)
    if not usuario.es_instructor:
        messages.error(request, 'No tienes permisos para ver este curso.')
        return redirect('home')
        
    curso = get_object_or_404(Curso, pk=pk, instructor=request.user)
    estudiantes = Compra.objects.filter(curso=curso, estado_pago='validado')
    
    context = {
        'curso': curso,
        'estudiantes': estudiantes,
        'total_estudiantes': estudiantes.count(),
    }
    
    return render(request, 'core/instructor/ver_curso.html', context)

@login_required
def ver_estadisticas_view(request: HttpRequest) -> HttpResponse:
    """Vista para ver estadísticas detalladas como instructor."""
    usuario = cast(Usuario, request.user)
    if not usuario.es_instructor:
        messages.error(request, 'No tienes permisos para ver estadísticas.')
        return redirect('home')
    
    # Obtener estadísticas detalladas
    cursos = Curso.objects.filter(instructor=request.user)
    total_estudiantes = Compra.objects.filter(
        curso__instructor=request.user,
        estado_pago='validado'
    ).values('estudiante').distinct().count()
    
    ingresos_por_curso = Compra.objects.filter(
        curso__instructor=request.user,
        estado_pago='validado'
    ).values('curso__titulo').annotate(
        total=Sum('monto_pagado')
    )
    
    context = {
        'cursos': cursos,
        'total_estudiantes': total_estudiantes,
        'ingresos_por_curso': ingresos_por_curso,
    }
    
    return render(request, 'core/instructor/estadisticas.html', context)

@login_required
def eliminar_curso_instructor(request: HttpRequest, pk: int) -> HttpResponse:
    """Vista para eliminar un curso como instructor."""
    usuario = cast(Usuario, request.user)
    if not usuario.es_instructor:
        messages.error(request, 'No tienes permisos para eliminar cursos.')
        return redirect('home')
    
    curso = get_object_or_404(Curso, pk=pk, instructor=request.user)
    
    if request.method == 'POST':
        curso.delete()
        return redirect('instructor_dashboard')
    
    return render(request, 'core/instructor/eliminar_curso.html', {'curso': curso})

@login_required
def create_course(request: HttpRequest) -> HttpResponse:
    """Vista para crear un nuevo curso."""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para crear cursos.')
        return redirect('admin_courses')
        
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            curso = form.save()
            messages.success(request, f'Curso "{curso.titulo}" creado exitosamente.')
            return redirect('admin_courses')
    else:
        form = CourseForm()
    
    return render(request, 'core/admin/create_course.html', {'form': form})

