from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import Usuario, Curso
from .translations import FORM_LABELS, ERROR_MESSAGES

class AdminUserCreationForm(UserCreationForm):
    TIPOS_USUARIO = [
        ('estudiante', 'Estudiante'),
        ('instructor', 'Instructor'),
        ('admin', 'Administrador')
    ]
    
    email = forms.EmailField(
        label=FORM_LABELS['email'],
        error_messages={'required': ERROR_MESSAGES['required'], 'invalid': ERROR_MESSAGES['invalid']}
    )
    nombre_completo = forms.CharField(
        label=FORM_LABELS['nombre_completo'],
        error_messages={'required': ERROR_MESSAGES['required']}
    )
    tipo_usuario = forms.ChoiceField(
        choices=TIPOS_USUARIO,
        label='Tipo de Usuario',
        error_messages={'required': 'Por favor, selecciona el tipo de usuario'}
    )
    titulo_especialidad = forms.CharField(
        label="Título o Especialidad",
        help_text="Solo para instructores. Ej: Profesor de Historia, Ingeniero en Sistemas",
        required=False
    )
    
    class Meta:
        model = Usuario
        fields = ('username', 'email', 'nombre_completo', 'tipo_usuario', 'titulo_especialidad', 'password1', 'password2')

    def clean(self):
        cleaned_data = super().clean()
        tipo_usuario = cleaned_data.get('tipo_usuario')
        titulo_especialidad = cleaned_data.get('titulo_especialidad')

        if tipo_usuario == 'instructor' and not titulo_especialidad:
            raise forms.ValidationError('El título o especialidad es requerido para instructores')
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.nombre_completo = self.cleaned_data['nombre_completo']
        
        tipo_usuario = self.cleaned_data['tipo_usuario']
        if tipo_usuario == 'estudiante':
            user.es_estudiante = True
        elif tipo_usuario == 'instructor':
            user.es_instructor = True
            user.titulo_especialidad = self.cleaned_data['titulo_especialidad']
        elif tipo_usuario == 'admin':
            user.is_superuser = True
            user.is_staff = True
        
        if commit:
            user.save()
        return user

class InstructorCreationForm(UserCreationForm):
    nombre_completo = forms.CharField(
        label=FORM_LABELS['nombre_completo'],
        error_messages={'required': ERROR_MESSAGES['required']}
    )
    titulo_especialidad = forms.CharField(
        label="Título o Especialidad",
        help_text="Ej: Profesor de Historia, Ingeniero en Sistemas, Diseñador Gráfico",
        error_messages={'required': 'Por favor, ingresa el título o especialidad del instructor'}
    )
    
    class Meta:
        model = Usuario
        fields = ('nombre_completo', 'titulo_especialidad')

    def save(self, commit=True):
        user = super().save(commit=False)
        # Generar username institucional basado en el nombre
        nombres = self.cleaned_data['nombre_completo'].split()
        if len(nombres) > 1:
            username = f"{nombres[0].lower()}.{nombres[-1].lower()}"
        else:
            username = nombres[0].lower()
        
        # Asegurarse de que el username sea único
        base_username = username
        counter = 1
        while Usuario.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        user.username = username
        user.email = f"{username}@conectasaber.edu"
        user.es_instructor = True
        user.titulo_especialidad = self.cleaned_data['titulo_especialidad']
        
        if commit:
            user.save()
        return user

class CourseForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['titulo', 'descripcion', 'precio', 'tipo']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'precio': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
        }
        labels = {
            'titulo': 'Título del Curso',
            'descripcion': 'Descripción',
            'precio': 'Precio',
            'tipo': 'Tipo de Curso'
        }
        help_texts = {
            'titulo': 'Ingresa un título descriptivo para el curso',
            'descripcion': 'Describe el contenido y objetivos del curso',
            'precio': 'Establece el precio en dólares',
            'tipo': 'Selecciona si el curso será grabado o en vivo'
        }

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
