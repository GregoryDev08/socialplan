from django import forms
from .models import Canal, Campana, Publicacion


class MixinBootstrap:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.TextInput, forms.EmailInput,
                                   forms.NumberInput, forms.URLInput,
                                   forms.PasswordInput, forms.DateInput,
                                   forms.DateTimeInput, forms.TimeInput)):
                widget.attrs.setdefault('class', 'form-control')
            elif isinstance(widget, forms.Textarea):
                widget.attrs.setdefault('class', 'form-control')
                widget.attrs.setdefault('rows', 4)
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault('class', 'form-select')
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault('class', 'form-check-input')
            elif isinstance(widget, forms.FileInput):
                widget.attrs.setdefault('class', 'form-control')


class CanalForm(MixinBootstrap, forms.ModelForm):
    class Meta:
        model  = Canal
        fields = ['nombre', 'icono']
        labels = {
            'nombre': 'Nombre del Canal',
            'icono':  'Clase CSS del Ícono',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej: Instagram, YouTube, Blog…', 'maxlength': 50}),
            'icono':  forms.TextInput(attrs={'placeholder': 'Ej: fab fa-instagram', 'maxlength': 50}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        if not nombre:
            raise forms.ValidationError('El nombre del canal no puede estar vacío.')
        qs = Canal.objects.filter(nombre__iexact=nombre)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(f'Ya existe un canal con el nombre "{nombre}".')
        return nombre


class CampanaForm(MixinBootstrap, forms.ModelForm):
    class Meta:
        model  = Campana
        fields = ['nombre', 'descripcion', 'fecha_inicio', 'fecha_fin', 'activa']
        labels = {
            'nombre':       'Nombre de la Campaña',
            'descripcion':  'Descripción',
            'fecha_inicio': 'Fecha de inicio',
            'fecha_fin':    'Fecha de fin',
            'activa':       'Campaña activa',
        }
        widgets = {
            'nombre':       forms.TextInput(attrs={'placeholder': 'Ej: Campaña Verano 2026', 'maxlength': 100}),
            'descripcion':  forms.Textarea(attrs={'placeholder': 'Objetivos, público objetivo, notas…', 'rows': 3}),
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'fecha_fin':    forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_inicio'].input_formats = ['%Y-%m-%d']
        self.fields['fecha_fin'].input_formats    = ['%Y-%m-%d']

    def clean(self):
        cleaned = super().clean()
        inicio  = cleaned.get('fecha_inicio')
        fin     = cleaned.get('fecha_fin')
        if inicio and fin and fin <= inicio:
            raise forms.ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')
        return cleaned


class PublicacionForm(MixinBootstrap, forms.ModelForm):
    class Meta:
        model  = Publicacion
        fields = [
            'titulo', 'contenido', 'imagen',
            'fecha_publicacion', 'estado',
            'canal', 'campana',
            'redactor', 'disenador',
            'engagement_rate', 'clics',
        ]
        labels = {
            'titulo':            'Título',
            'contenido':         'Texto / Descripción',
            'imagen':            'Imagen Destacada',
            'fecha_publicacion': 'Fecha y hora de publicación',
            'estado':            'Estado',
            'canal':             'Canal',
            'campana':           'Campaña',
            'redactor':          'Redactor',
            'disenador':         'Diseñador',
            'engagement_rate':   'Engagement Rate (%)',
            'clics':             'Clics',
        }
        widgets = {
            'titulo':    forms.TextInput(attrs={'placeholder': 'Escribe un título llamativo…', 'maxlength': 200}),
            'contenido': forms.Textarea(attrs={'placeholder': 'Cuerpo del post, caption para redes o artículo completo…', 'rows': 6}),
            'fecha_publicacion': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'engagement_rate':   forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '100'}),
            'clics':             forms.NumberInput(attrs={'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['fecha_publicacion'].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M']
        self.fields['campana'].required    = False
        self.fields['campana'].empty_label = '— Sin campaña —'
        self.fields['redactor'].required   = False
        self.fields['redactor'].empty_label = '— Sin asignar —'
        self.fields['disenador'].required  = False
        self.fields['disenador'].empty_label = '— Sin asignar —'
        self.fields['campana'].queryset    = Campana.objects.filter(activa=True)

        if user is not None:
            perfil = getattr(getattr(user, 'perfil', None), 'rol', 'redactor')
            if perfil in ('redactor', 'disenador'):
                allowed_estado = [
                    ('borrador', 'Borrador'),
                    ('revision', 'En Revisión'),
                ]
            else:
                allowed_estado = list(self.fields['estado'].choices)
            if self.instance.pk and self.instance.estado not in dict(allowed_estado):
                allowed_estado.append((self.instance.estado, self.instance.get_estado_display()))
            self.fields['estado'].choices = allowed_estado

    def clean_titulo(self):
        titulo = self.cleaned_data['titulo'].strip()
        if not titulo:
            raise forms.ValidationError('El título no puede estar vacío.')
        return titulo

    def clean_engagement_rate(self):
        tasa = self.cleaned_data.get('engagement_rate', 0.0)
        if tasa < 0 or tasa > 100:
            raise forms.ValidationError('El engagement rate debe estar entre 0 y 100.')
        return tasa
