from django.db import models
from django.contrib.auth.models import User

class PerfilUsuario(models.Model):
    ROLES = (
        ('redactor', 'Redactor'),
        ('disenador', 'Diseñador'),
        ('aprobador', 'Aprobador / Manager'),
    )
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROLES, default='redactor')
    biografia = models.TextField(blank=True)

    def __str__(self):
        return f"{self.usuario.username} ({self.get_rol_display()})"