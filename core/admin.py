from django.contrib import admin
from .models import Usuario, Curso, Modulo, Compra, Progreso, Evaluacion, Certificado


# ======= Usuario Admin =======
@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('username', 'nombre_completo', 'es_estudiante', 'es_instructor', 'es_administrador')
    list_filter = ('es_estudiante', 'es_instructor', 'es_administrador', 'date_joined')
    search_fields = ('nombre_completo', 'username', 'email')
    fieldsets = (
        ('Información de Usuario', {
            'fields': ('username', 'email', 'password')
        }),
        ('Información Personal', {
            'fields': ('nombre_completo', 'first_name', 'last_name')
        }),
        ('Roles', {
            'fields': ('es_estudiante', 'es_instructor', 'es_administrador')
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Fechas Importantes', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )


# ======= Curso Admin =======
@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'instructor', 'tipo', 'precio', 'fecha_creacion')
    list_filter = ('tipo', 'fecha_creacion', 'instructor')
    search_fields = ('titulo', 'descripcion', 'instructor__nombre_completo')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    fieldsets = (
        ('Información del Curso', {
            'fields': ('instructor', 'titulo', 'descripcion', 'tipo')
        }),
        ('Precio', {
            'fields': ('precio',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )


# ======= Modulo Admin =======
@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'curso', 'orden', 'fecha_creacion')
    list_filter = ('curso', 'fecha_creacion')
    search_fields = ('titulo', 'curso__titulo')
    readonly_fields = ('fecha_creacion',)
    fieldsets = (
        ('Información del Módulo', {
            'fields': ('curso', 'titulo', 'orden')
        }),
        ('Contenido', {
            'fields': ('contenido_url',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        }),
    )


# ======= Compra Admin =======
@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'curso', 'monto_pagado', 'estado_pago', 'fecha_compra')
    list_filter = ('estado_pago', 'fecha_compra', 'curso')
    search_fields = ('estudiante__nombre_completo', 'curso__titulo')
    readonly_fields = ('fecha_compra',)
    fieldsets = (
        ('Información de Compra', {
            'fields': ('estudiante', 'curso')
        }),
        ('Pago', {
            'fields': ('monto_pagado', 'estado_pago')
        }),
        ('Fechas', {
            'fields': ('fecha_compra',),
            'classes': ('collapse',)
        }),
    )


# ======= Progreso Admin =======
@admin.register(Progreso)
class ProgresoAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'modulo', 'completado', 'fecha_inicio')
    list_filter = ('completado', 'fecha_inicio')
    search_fields = ('estudiante__nombre_completo', 'modulo__titulo')
    readonly_fields = ('fecha_inicio',)
    fieldsets = (
        ('Información de Progreso', {
            'fields': ('estudiante', 'modulo')
        }),
        ('Estado', {
            'fields': ('completado', 'fecha_completado')
        }),
        ('Fechas', {
            'fields': ('fecha_inicio',),
            'classes': ('collapse',)
        }),
    )


# ======= Evaluacion Admin =======
@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'modulo', 'fecha_creacion')
    list_filter = ('fecha_creacion',)
    search_fields = ('titulo', 'modulo__titulo')
    readonly_fields = ('fecha_creacion',)
    fieldsets = (
        ('Información de Evaluación', {
            'fields': ('modulo', 'titulo')
        }),
        ('Descripción', {
            'fields': ('descripcion',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        }),
    )


# ======= Certificado Admin =======
@admin.register(Certificado)
class CertificadoAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'curso', 'fecha_emision', 'codigo_unico_pdf')
    list_filter = ('fecha_emision', 'curso')
    search_fields = ('estudiante__nombre_completo', 'curso__titulo', 'codigo_unico_pdf')
    readonly_fields = ('fecha_emision', 'codigo_unico_pdf')
    fieldsets = (
        ('Información del Certificado', {
            'fields': ('estudiante', 'curso', 'codigo_unico_pdf')
        }),
        ('Fechas', {
            'fields': ('fecha_emision',),
            'classes': ('collapse',)
        }),
    )
