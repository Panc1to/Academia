from django.db import models
from django.contrib.auth.models import AbstractUser


# ======= 1. Usuario =======
class Usuario(AbstractUser):
    nombre_completo = models.CharField(max_length=100)
    es_estudiante = models.BooleanField(default=False)
    es_instructor = models.BooleanField(default=False)
    es_administrador = models.BooleanField(default=False)
    titulo_especialidad = models.CharField(max_length=100, blank=True, null=True, help_text="Título o especialidad del instructor (ej: 'Profesor de Historia', 'Ingeniero en Sistemas')")

    def __str__(self):
        if self.es_instructor and self.titulo_especialidad:
            return f"{self.nombre_completo} - {self.titulo_especialidad}"
        return f"{self.nombre_completo}"


# ======= 2. Curso =======
from django.utils.text import slugify

class Curso(models.Model):
    instructor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='cursos')
    titulo = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(
        max_length=20,
        choices=[('grabado', 'Grabado'), ('en vivo', 'En vivo')]
    )
    estado = models.CharField(
        max_length=20,
        choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')],
        default='activo'
    )
    link_material = models.URLField(blank=True, null=True, help_text="Link opcional para material adicional del curso")
    archivo_pdf = models.FileField(upload_to='cursos/pdfs/', blank=True, null=True, help_text="Archivo PDF opcional para el curso")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
            # Asegurar que el slug sea único
            counter = 1
            while Curso.objects.filter(slug=self.slug).exists():
                self.slug = f"{slugify(self.titulo)}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo

    class Meta:
        ordering = ['-fecha_creacion']


# ======= 3. Modulo =======
class Modulo(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='modulos')
    titulo = models.CharField(max_length=100)
    contenido_url = models.TextField()
    orden = models.PositiveIntegerField(default=1)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.curso.titulo} - {self.titulo}"

    class Meta:
        ordering = ['orden']
        unique_together = ('curso', 'orden')


# ======= 4. Compra =======
class Compra(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('validado', 'Validado'),
        ('rechazado', 'Rechazado'),
    ]

    estudiante = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='compras')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='compras')
    fecha_compra = models.DateTimeField(auto_now_add=True)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2)
    estado_pago = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')

    def __str__(self):
        return f"{self.estudiante.nombre_completo} - {self.curso.titulo}"

    class Meta:
        ordering = ['-fecha_compra']
        unique_together = ('estudiante', 'curso')


# ======= 5. Progreso =======
class Progreso(models.Model):
    estudiante = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='progresos')
    modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE, related_name='progresos')
    completado = models.BooleanField(default=False)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_completado = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.estudiante.nombre_completo} - {self.modulo.titulo}"

    class Meta:
        unique_together = ('estudiante', 'modulo')
        ordering = ['-fecha_inicio']


# ======= 6. Evaluacion =======
class Evaluacion(models.Model):
    modulo = models.OneToOneField(Modulo, on_delete=models.CASCADE, related_name='evaluacion')
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evaluación - {self.titulo}"


# ======= 7. Plantilla de Certificado =======
import os
from django.utils.text import slugify

class PlantillaCertificado(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    archivo = models.FileField(upload_to='certificados/plantillas/')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def delete(self, *args, **kwargs):
        # Delete the file when the model instance is deleted
        if self.archivo:
            if os.path.isfile(self.archivo.path):
                os.remove(self.archivo.path)
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['-fecha_creacion']

# ======= 8. Certificado =======
class Certificado(models.Model):
    estudiante = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='certificados')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='certificados')
    fecha_emision = models.DateField(auto_now_add=True)
    codigo_unico_pdf = models.CharField(max_length=100, unique=True)
    archivo = models.FileField(upload_to='certificados/emitidos/')

    def __str__(self):
        return f"Certificado - {self.estudiante.nombre_completo} ({self.curso.titulo})"

    class Meta:
        ordering = ['-fecha_emision']
        unique_together = ('estudiante', 'curso')
