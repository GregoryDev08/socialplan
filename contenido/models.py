from django.db import models
from django.contrib.auth.models import User

class Canal(models.Model):
    nombre = models.CharField(max_length=50)
    icono = models.CharField(max_length=50, blank=True)
    class Meta:
        verbose_name_plural = "Canales"
    def __str__(self):
        return self.nombre
class Campana(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activa = models.BooleanField(default=True)
    def __str__(self):
        return self.nombre
class Publicacion(models.Model):
    ESTADOS = (
        ('borrador', 'Borrador'),
        ('revision', 'En Revisión'),
        ('aprobado', 'Aprobado'),
        ('publicado', 'Publicado'),
    )

    titulo = models.CharField(max_length=200)
    contenido = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='publicaciones/', blank=True, null=True)
    fecha_publicacion = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='borrador')
    canal = models.ForeignKey(Canal, on_delete=models.CASCADE, related_name='publicaciones')
    campana = models.ForeignKey(Campana, on_delete=models.SET_NULL, null=True, blank=True, related_name='publicaciones')
    redactor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='redacciones')
    disenador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='disenos')
    engagement_rate = models.FloatField(default=0.0)
    clics = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Publicaciones"

    def __str__(self):
        return f"{self.titulo} [{self.canal.nombre}]"