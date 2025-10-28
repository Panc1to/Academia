from django.shortcuts import redirect
from django.http import HttpRequest

def handler404(request: HttpRequest, exception=None):
    """
    Manejador personalizado para errores 404 (página no encontrada).
    Redirige al usuario a la página de inicio.
    """
    return redirect('home')