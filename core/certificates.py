from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Certificado
from django.db.models import Count

@login_required
def create_certificate_template(request):
    """Vista para crear una nueva plantilla de certificado."""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para crear plantillas de certificados.')
        return redirect('admin_certificates')

    if request.method == 'POST':
        # Aquí irá la lógica para crear la plantilla
        messages.success(request, 'Plantilla creada exitosamente.')
        return redirect('admin_certificates')

    return render(request, 'core/admin/create_certificate_template.html')