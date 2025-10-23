from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import Usuario
from .translations import FORM_LABELS, ERROR_MESSAGES

class EstudianteRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label=FORM_LABELS['email'],
        error_messages={'required': ERROR_MESSAGES['required'], 'invalid': ERROR_MESSAGES['invalid']}
    )
    nombre_completo = forms.CharField(
        label=FORM_LABELS['nombre_completo'],
        error_messages={'required': ERROR_MESSAGES['required']}
    )
    password1 = forms.CharField(
        label=_('Contraseña'),
        widget=forms.PasswordInput,
        error_messages={'required': ERROR_MESSAGES['required']}
    )
    password2 = forms.CharField(
        label=_('Confirmar contraseña'),
        widget=forms.PasswordInput,
        error_messages={'required': ERROR_MESSAGES['required']}
    )

    class Meta:
        model = Usuario
        fields = ('username', 'email', 'nombre_completo', 'password1', 'password2')
        labels = {
            'username': FORM_LABELS['username'],
        }
        error_messages = {
            'username': {
                'unique': ERROR_MESSAGES['unique'],
                'required': ERROR_MESSAGES['required'],
            }
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = _('Requerido. 150 caracteres o menos. Letras, números y @/./+/-/_ solamente.')
        self.fields['password1'].help_text = _('La contraseña debe tener al menos 8 caracteres.')
        self.fields['password2'].help_text = _('Ingresa la misma contraseña que antes, para verificación.')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.es_estudiante = True
        if commit:
            user.save()
        return user
