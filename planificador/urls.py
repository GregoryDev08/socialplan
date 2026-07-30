from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from contenido.views import inicio_view

urlpatterns = [
    path('admin/',admin.site.urls),
    path('',login_required(inicio_view),name='inicio'),
    path('contenido/',include('contenido.urls')),
    path('cuentas/',include('cuentas.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
