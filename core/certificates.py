from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Certificado, PlantillaCertificado
from django.db.models import Count
import os

@login_required
def create_certificate_template(request):
    """Vista para crear una nueva plantilla de certificado."""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para crear plantillas de certificados.')
        return redirect('admin_certificates')

    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre')
            descripcion = request.POST.get('descripcion', '')  # Optional field
            archivo = request.FILES.get('archivo')
            
            # Validate required fields
            if not nombre:
                messages.error(request, 'El nombre de la plantilla es requerido.')
                return render(request, 'core/admin/create_certificate_template.html')
            
            if not archivo:
                messages.error(request, 'Debe seleccionar un archivo PDF.')
                return render(request, 'core/admin/create_certificate_template.html')
            
            # Validate file type
            if not archivo.name.lower().endswith('.pdf'):
                messages.error(request, 'El archivo debe ser un PDF válido.')
                return render(request, 'core/admin/create_certificate_template.html')
            
            # Check file size (max 5MB)
            if archivo.size > 5 * 1024 * 1024:
                messages.error(request, 'El archivo es demasiado grande. El tamaño máximo permitido es 5MB.')
                return render(request, 'core/admin/create_certificate_template.html')
            
            # Create new template
            plantilla = PlantillaCertificado.objects.create(
                nombre=nombre,
                descripcion=descripcion,
                archivo=archivo
            )
            
            messages.success(request, f'Plantilla "{plantilla.nombre}" creada exitosamente.')
            return redirect('admin_certificates')
                
        except Exception as e:
            messages.error(request, f'Error al crear la plantilla: {str(e)}')
            return render(request, 'core/admin/create_certificate_template.html')

    return render(request, 'core/admin/create_certificate_template.html')


@login_required
def delete_certificate_template(request, pk):
    """Vista para eliminar una plantilla de certificado."""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para eliminar plantillas de certificados.')
        return redirect('admin_certificates')

    plantilla = get_object_or_404(PlantillaCertificado, pk=pk)

    if request.method == 'POST':
        try:
            # Guardar el nombre para el mensaje
            nombre_plantilla = plantilla.nombre
            
            # Eliminar el archivo físico si existe
            if plantilla.archivo:
                archivo_path = plantilla.archivo.path
                if os.path.exists(archivo_path):
                    os.remove(archivo_path)
            
            # Eliminar el registro de la base de datos
            plantilla.delete()
            
            messages.success(request, f'La plantilla "{nombre_plantilla}" ha sido eliminada exitosamente.')
            
        except Exception as e:
            messages.error(request, f'Error al eliminar la plantilla: {str(e)}')
    
    return redirect('admin_certificates')
