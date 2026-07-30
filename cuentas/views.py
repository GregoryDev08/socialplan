from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from .models import PerfilUsuario


def login_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')

    login_error = False

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or '/'
            return redirect(next_url)
        else:
            login_error = True
            messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'login.html', {
        'login_error': login_error,
        'next': request.GET.get('next', ''),
    })


def logout_view(request):
    if request.user.is_authenticated:
        messages.success(request, f'¡Hasta pronto, {request.user.username}!')
    logout(request)
    return redirect('cuentas:login')


@login_required
def perfil_view(request):
    perfil, _ = PerfilUsuario.objects.get_or_create(usuario=request.user)

    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name  = request.POST.get('last_name', '').strip()
        user.email      = request.POST.get('email', '').strip()
        user.save(update_fields=['first_name', 'last_name', 'email'])

        perfil.rol       = request.POST.get('rol', perfil.rol)
        perfil.biografia = request.POST.get('biografia', '').strip()
        perfil.save(update_fields=['rol', 'biografia'])

        password_nuevo = request.POST.get('password_nuevo', '').strip()
        if password_nuevo:
            password_conf = request.POST.get('password_conf', '').strip()
            if password_nuevo != password_conf:
                messages.error(request, 'Las contraseñas no coinciden.')
                return render(request, 'cuentas/perfil.html', {'perfil': perfil})
            if len(password_nuevo) < 8:
                messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
                return render(request, 'cuentas/perfil.html', {'perfil': perfil})
            user.set_password(password_nuevo)
            user.save(update_fields=['password'])
            messages.warning(request, 'Contraseña actualizada. Inicia sesión nuevamente.')
            logout(request)
            return redirect('cuentas:login')

        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('cuentas:perfil')

    from contenido.models import Publicacion
    mis_publicaciones = (
        Publicacion.objects
        .select_related('canal')
        .filter(redactor=request.user)
        .order_by('-fecha_publicacion')[:5]
    )

    return render(request, 'cuentas/perfil.html', {
        'perfil':           perfil,
        'mis_publicaciones': mis_publicaciones,
    })
