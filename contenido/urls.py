from django.urls import path
from . import views

app_name = 'contenido'

urlpatterns = [
    path('calendario/',views.calendario_view,name='calendario'),
    path('aprobaciones/',views.aprobaciones_view,name='aprobaciones'),
    path('publicaciones/',views.publicaciones_list,name='publicaciones_list'),
    path('publicaciones/nueva/',views.publicaciones_create,name='publicaciones_create'),
    path('publicaciones/<int:pk>/editar/',views.publicaciones_edit,name='publicaciones_edit'),
    path('publicaciones/<int:pk>/eliminar/',views.publicaciones_delete,name='publicaciones_delete'),
    path('publicaciones/<int:pk>/estado/',views.cambiar_estado,name='cambiar_estado'),
    path('publicaciones/<int:pk>/accion-rapida/<str:nuevo_estado>/', views.accion_rapida_post, name='accion_rapida_post'),
    path('canales/',views.canales_list,name='canales_list'),
    path('canales/nuevo/',views.canales_create,name='canales_create'),
    path('canales/<int:pk>/editar/',views.canales_edit,name='canales_edit'),
    path('canales/<int:pk>/eliminar/',views.canales_delete,name='canales_delete'),
    path('campanas/',views.campanas_list,name='campanas_list'),
    path('campanas/nueva/',views.campanas_create,name='campanas_create'),
    path('campanas/<int:pk>/editar/',views.campanas_edit,name='campanas_edit'),
    path('campanas/<int:pk>/eliminar/',views.campanas_delete,name='campanas_delete'),
    path('api/eventos/',views.api_eventos,name='api_eventos'),
    path('api/mover/',views.api_mover_evento,name='api_mover_evento'),
]
