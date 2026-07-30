from django.contrib import admin
from .models import Canal, Campana, Publicacion

@admin.register(Canal)
class CanalAdmin(admin.ModelAdmin):
    lista_despliegue = ('nombre', 'icono')

@admin.register(Campana)
class CampanaAdmin(admin.ModelAdmin):
    lista_despliegue = ('nombre', 'fecha_inicio', 'fecha_fin', 'activa')

@admin.register(Publicacion)
class PublicacionAdmin(admin.ModelAdmin):
    lista_despliegue = ('titulo', 'canal', 'estado', 'fecha_publicacion', 'redactor')
    lista_filtros = ('canal', 'estado', 'campana')
    campos_busqueda = ('titulo', 'contenido')