from django.shortcuts import render
from django.http import HttpRequest, HttpResponse


def home(request: HttpRequest) -> HttpResponse:
	"""Página de inicio simple.

	Renderiza una plantilla básica para verificar que las vistas funcionan.
	"""
	return render(request, "core/index.html", {"title": "Conecta Saber"})
