# coding: utf-8

from django.utils.translation import gettext_lazy as _

# Mensajes de error y validación
ERROR_MESSAGES = {
    'required': _('Este campo es obligatorio.'),
    'invalid': _('Valor inválido.'),
    'unique': _('Ya existe un usuario con este valor.'),
    'password_mismatch': _('Las contraseñas no coinciden.'),
    'min_length': _('Este campo debe tener al menos %(limit_value)d caracteres.'),
    'max_length': _('Este campo debe tener como máximo %(limit_value)d caracteres.'),
}

# Etiquetas de formularios
FORM_LABELS = {
    'username': _('Nombre de usuario'),
    'email': _('Correo electrónico'),
    'password': _('Contraseña'),
    'password_confirm': _('Confirmar contraseña'),
    'nombre_completo': _('Nombre completo'),
}