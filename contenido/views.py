import json
from calendar import monthrange
from datetime import date, datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.timezone import make_aware
from django.views.decorators.http import require_POST
from .forms import CampanaForm, CanalForm, PublicacionForm
from .models import Campana, Canal, Publicacion

ICONOS_SUGERIDOS = [
    ('fab fa-instagram', 'Instagram'),
    ('fab fa-youtube', 'YouTube'),
    ('fab fa-tiktok', 'TikTok'),
    ('fab fa-twitter', 'Twitter / X'),
    ('fab fa-facebook', 'Facebook'),
    ('fab fa-linkedin', 'LinkedIn'),
    ('fab fa-pinterest', 'Pinterest'),
    ('fab fa-twitch', 'Twitch'),
    ('bx bx-globe', 'Blog / Web'),
    ('bx bx-rss', 'Newsletter'),
    ('fab fa-telegram', 'Telegram'),
    ('fab fa-whatsapp', 'WhatsApp'),
]


def get_user_role(user):
    if not user or not user.is_authenticated:
        return None
    return getattr(getattr(user, 'perfil', None), 'rol', None) or 'redactor'


def role_required(*roles):
    def check(user):
        return get_user_role(user) in roles
    return user_passes_test(check, login_url='login', redirect_field_name=None)


def can_transition(user, publicacion, nuevo_estado):
    rol = get_user_role(user)
    origen = publicacion.estado
    if rol == 'aprobador':
        return nuevo_estado in ['aprobado', 'publicado'] or (origen in ['borrador', 'revision'] and nuevo_estado in ['borrador', 'revision'])
    if rol == 'disenador':
        return nuevo_estado in ['borrador', 'revision']
    if rol == 'redactor':
        return origen == 'borrador' and nuevo_estado == 'revision'
    return False


@login_required
def inicio_view(request):
    hoy = timezone.now()
    estadisticas = {
        'total_publicaciones': Publicacion.objects.count(),
        'publicadas': Publicacion.objects.filter(estado='publicado').count(),
        'en_revision': Publicacion.objects.filter(estado='revision').count(),
        'campanas_activas': Campana.objects.filter(activa=True).count(),
    }
    ultimas_publicaciones = (
        Publicacion.objects
        .select_related('canal', 'campana', 'redactor')
        .order_by('-fecha_publicacion')[:8]
    )
    current_month_start = date(hoy.year, hoy.month, 1)
    next_month_year = hoy.year + 1 if hoy.month == 12 else hoy.year
    next_month = 1 if hoy.month == 12 else hoy.month + 1
    last_day_next_month = monthrange(next_month_year, next_month)[1]
    next_month_end = date(next_month_year, next_month, last_day_next_month)

    canales_annotados = (
        Canal.objects
        .annotate(total=Count(
            'publicaciones',
            filter=Q(
                publicaciones__fecha_publicacion__date__range=(current_month_start, next_month_end)
            )
        ))
        .order_by('-total')
    )
    maximo_total = max((c.total for c in canales_annotados), default=1) or 1
    frecuencia_canales = [
        {'canal': c, 'total': c.total, 'porcentaje': round(c.total / maximo_total * 100)}
        for c in canales_annotados
    ]
    etiquetas_grafico = []
    datos_engagement = []
    datos_clics = []
    try:
        from dateutil.relativedelta import relativedelta
        offsets = range(-3, 4)
        for offset in offsets:
            mes = hoy + relativedelta(months=offset)
            qs = Publicacion.objects.filter(
                fecha_publicacion__month=mes.month,
                fecha_publicacion__year=mes.year,
            )
            etiquetas_grafico.append(mes.strftime('%b'))
            datos_engagement.append(round(qs.aggregate(v=Avg('engagement_rate'))['v'] or 0, 2))
            datos_clics.append(qs.aggregate(v=Sum('clics'))['v'] or 0)
    except ImportError:
        for offset in range(-3, 4):
            total_month = hoy.month + offset
            mes_num = ((total_month - 1) % 12) + 1
            mes_year = hoy.year + ((total_month - 1) // 12)
            if total_month <= 0 and total_month % 12 != 0:
                mes_year -= 1
            qs = Publicacion.objects.filter(
                fecha_publicacion__month=mes_num,
                fecha_publicacion__year=mes_year,
            )
            etiquetas_grafico.append(date(mes_year, mes_num, 1).strftime('%b'))
            datos_engagement.append(round(qs.aggregate(v=Avg('engagement_rate'))['v'] or 0, 2))
            datos_clics.append(qs.aggregate(v=Sum('clics'))['v'] or 0)

    estados_map = {
        'borrador':  'Borrador',
        'revision':  'En Revisión',
        'aprobado':  'Aprobado',
        'publicado': 'Publicado',
    }
    estados_labels = json.dumps(list(estados_map.values()))
    estados_data = json.dumps([
        Publicacion.objects.filter(estado=k).count() for k in estados_map.keys()
    ])

    return render(request, 'inicio.html', {
        'stats': estadisticas,
        'ultimas_publicaciones': ultimas_publicaciones,
        'frecuencia_canales': frecuencia_canales,
        'etiquetas_grafico': json.dumps(etiquetas_grafico),
        'datos_engagement': json.dumps(datos_engagement),
        'datos_clics': json.dumps(datos_clics),
        'etiquetas_canales': json.dumps([c.nombre for c in canales_annotados]),
        'datos_canales': json.dumps([Publicacion.objects.filter(canal=c).count() for c in canales_annotados]),
        'etiquetas_estados': estados_labels,
        'datos_estados': estados_data,
    })


@login_required
def publicaciones_list(request):
    publicaciones_qs = Publicacion.objects.select_related('canal', 'campana', 'redactor').order_by('-fecha_publicacion')
    pk_campana = request.GET.get('campana')
    if pk_campana:
        publicaciones_qs = publicaciones_qs.filter(campana__pk=pk_campana)
    return render(request, 'contenido/publicaciones_list.html', {'publicaciones': publicaciones_qs})


@login_required
def publicaciones_create(request):
    initial = {}
    fecha = request.GET.get('fecha', '')
    if fecha:
        if 'T' not in fecha and len(fecha) == 10:
            fecha = f'{fecha}T09:00'
        initial['fecha_publicacion'] = fecha
    form = PublicacionForm(initial=initial, user=request.user)
    if request.method == 'POST':
        form = PublicacionForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            publicacion = form.save(commit=False)
            if not publicacion.redactor:
                publicacion.redactor = request.user
            publicacion.save()
            messages.success(request, f'Publicación "{publicacion.titulo}" creada.')
            return redirect('contenido:publicaciones_list')
    return render(request, 'contenido/publicaciones_form.html', {
        'form':     form,
        'canales':  Canal.objects.all(),
        'campanas': Campana.objects.filter(activa=True),
        'usuarios': User.objects.filter(is_active=True).order_by('username'),
    })


@login_required
def publicaciones_edit(request, pk):
    publicacion = get_object_or_404(Publicacion, pk=pk)
    form = PublicacionForm(instance=publicacion, user=request.user)
    if request.method == 'POST':
        form = PublicacionForm(request.POST, request.FILES, instance=publicacion, user=request.user)
        if form.is_valid():
            publicacion = form.save()
            messages.success(request, f'Publicación "{publicacion.titulo}" actualizada.')
            return redirect('contenido:publicaciones_list')
    return render(request, 'contenido/publicaciones_form.html', {
        'form': form,
        'publicacion': publicacion,
        'canales': Canal.objects.all(),
        'campanas': Campana.objects.filter(activa=True),
        'usuarios': User.objects.filter(is_active=True).order_by('username'),
    })


@login_required
@require_POST
def publicaciones_delete(request, pk):
    publicacion = get_object_or_404(Publicacion, pk=pk)
    titulo = publicacion.titulo
    publicacion.delete()
    messages.success(request, f'Publicación "{titulo}" eliminada.')
    return redirect('contenido:publicaciones_list')


@login_required
def canales_list(request):
    canales = Canal.objects.prefetch_related('publicaciones').all()
    return render(request, 'contenido/canales_list.html', {'canales': canales})


@login_required
def canales_create(request):
    form = CanalForm()
    if request.method == 'POST':
        form = CanalForm(request.POST)
        if form.is_valid():
            canal = form.save()
            messages.success(request, f'Canal "{canal.nombre}" creado.')
            return redirect('contenido:canales_list')
    return render(request, 'contenido/canales_form.html', {
        'form': form,
        'iconos_sugeridos': ICONOS_SUGERIDOS,
    })


@login_required
def canales_edit(request, pk):
    canal = get_object_or_404(Canal, pk=pk)
    form = CanalForm(instance=canal)
    if request.method == 'POST':
        form = CanalForm(request.POST, instance=canal)
        if form.is_valid():
            canal = form.save()
            messages.success(request, f'Canal "{canal.nombre}" actualizado.')
            return redirect('contenido:canales_list')
    return render(request, 'contenido/canales_form.html', {
        'form': form,
        'canal': canal,
        'iconos_sugeridos': ICONOS_SUGERIDOS,
    })


@login_required
@require_POST
def canales_delete(request, pk):
    canal = get_object_or_404(Canal, pk=pk)
    nombre = canal.nombre
    canal.delete()
    messages.success(request, f'Canal "{nombre}" eliminado.')
    return redirect('contenido:canales_list')


@login_required
def campanas_list(request):
    campanas = Campana.objects.prefetch_related('publicaciones').order_by('fecha_inicio')
    return render(request, 'contenido/campanas_list.html', {'campanas': campanas})


@login_required
def campanas_create(request):
    form = CampanaForm()
    if request.method == 'POST':
        form = CampanaForm(request.POST)
        if form.is_valid():
            campana = form.save()
            messages.success(request, f'Campaña "{campana.nombre}" creada.')
            return redirect('contenido:campanas_list')
    return render(request, 'contenido/campanas_form.html', {'form': form})


@login_required
def campanas_edit(request, pk):
    campana = get_object_or_404(Campana, pk=pk)
    form = CampanaForm(instance=campana)
    if request.method == 'POST':
        form = CampanaForm(request.POST, instance=campana)
        if form.is_valid():
            campana = form.save()
            messages.success(request, f'Campaña "{campana.nombre}" actualizada.')
            return redirect('contenido:campanas_list')
    return render(request, 'contenido/campanas_form.html', {'form': form, 'campana': campana})


@login_required
@require_POST
def campanas_delete(request, pk):
    campana = get_object_or_404(Campana, pk=pk)
    nombre = campana.nombre
    campana.delete()
    messages.success(request, f'Campaña "{nombre}" eliminada.')
    return redirect('contenido:campanas_list')


@login_required
def calendario_view(request):
    posts_pendientes = (
        Publicacion.objects
        .select_related('canal')
        .filter(estado__in=['borrador', 'revision'])
        .order_by('fecha_publicacion')[:30]
    )
    canales = Canal.objects.all()
    return render(request, 'contenido/calendario.html', {
        'canales':          canales,
        'posts_sin_fecha':  posts_pendientes,
    })


@login_required
@role_required('aprobador')
def aprobaciones_view(request):
    pendientes = (
        Publicacion.objects
        .select_related('canal', 'campana', 'redactor')
        .filter(estado='revision')
        .order_by('fecha_publicacion')
    )
    historial = (
        Publicacion.objects
        .select_related('canal', 'campana', 'redactor')
        .filter(estado__in=['aprobado', 'publicado', 'borrador'])
        .order_by('-fecha_publicacion')
    )
    return render(request, 'contenido/aprobaciones.html', {
        'pendientes': pendientes,
        'historial': historial,
    })


@login_required
@role_required('aprobador')
@require_POST
def accion_rapida_post(request, pk, nuevo_estado):
    pub = get_object_or_404(Publicacion, pk=pk)
    if nuevo_estado == 'rechazado':
        nuevo_estado = 'borrador'
    estados_validos = ['aprobado', 'publicado', 'borrador']
    if nuevo_estado not in estados_validos:
        messages.error(request, 'Estado inválido.')
        return redirect('contenido:aprobaciones')
    if not can_transition(request.user, pub, nuevo_estado):
        messages.error(request, 'No tienes permiso para cambiar ese estado.')
        return redirect('contenido:aprobaciones')
    pub.estado = nuevo_estado
    pub.save(update_fields=['estado'])
    messages.success(request, f'Publicación "{pub.titulo}" actualizada a "{pub.get_estado_display()}".')
    return redirect(request.META.get('HTTP_REFERER') or 'contenido:aprobaciones')


@login_required
@require_POST
def cambiar_estado(request, pk):
    pub = get_object_or_404(Publicacion, pk=pk)
    nuevo_estado = request.POST.get('estado')
    estados_validos = [e[0] for e in Publicacion.ESTADOS]
    if nuevo_estado not in estados_validos:
        return JsonResponse({'ok': False, 'error': 'Estado inválido.'}, status=400)
    if not can_transition(request.user, pub, nuevo_estado):
        return JsonResponse({'ok': False, 'error': 'No tienes permiso para cambiar a ese estado.'}, status=403)
    pub.estado = nuevo_estado
    pub.save(update_fields=['estado'])
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'estado': pub.estado})
    messages.success(request, f'Estado actualizado a "{pub.get_estado_display()}".')
    return redirect(request.POST.get('next', 'contenido:publicaciones_list'))


@login_required
def api_eventos(request):
    qs = Publicacion.objects.select_related('canal', 'campana').all()
    inicio_str = request.GET.get('start')
    fin_str = request.GET.get('end')
    if inicio_str:
        try:
            qs = qs.filter(fecha_publicacion__gte=datetime.fromisoformat(inicio_str.replace('Z', '+00:00')))
        except ValueError:
            pass
    if fin_str:
        try:
            qs = qs.filter(fecha_publicacion__lte=datetime.fromisoformat(fin_str.replace('Z', '+00:00')))
        except ValueError:
            pass
    pk_canal = request.GET.get('canal')
    if pk_canal:
        qs = qs.filter(canal__pk=pk_canal)
    estado = request.GET.get('estado')
    if estado:
        qs = qs.filter(estado=estado)

    COLORES = {
        'borrador': '#8592a3',
        'revision': '#ffab00',
        'aprobado': '#696cff',
        'publicado': '#71dd37',
    }
    eventos = [
        {
            'id': publicacion.pk,
            'title': publicacion.titulo,
            'start': publicacion.fecha_publicacion.isoformat(),
            'color': COLORES.get(publicacion.estado, '#696cff'),
            'classNames': [f'ev-{publicacion.estado}'],
            'extendedProps': {
                'pubId': publicacion.pk,
                'estado': publicacion.estado,
                'canal': publicacion.canal.nombre,
                'campana': publicacion.campana.nombre if publicacion.campana else '',
                'engagement': publicacion.engagement_rate,
            },
        }
        for publicacion in qs
    ]
    return JsonResponse(eventos, safe=False)


@login_required
@require_POST
def api_mover_evento(request):
    try:
        datos = json.loads(request.body)
        id_publicacion = int(datos['id'])
        fecha_str = datos['fecha']
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        return JsonResponse({'ok': False, 'error': f'Datos inválidos: {exc}'}, status=400)

    publicacion = get_object_or_404(Publicacion, pk=id_publicacion)
    try:
        if 'T' in fecha_str:
            nueva_fecha = datetime.fromisoformat(fecha_str)
        else:
            nueva_fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
            if publicacion.fecha_publicacion:
                nueva_fecha = nueva_fecha.replace(
                    hour=publicacion.fecha_publicacion.hour,
                    minute=publicacion.fecha_publicacion.minute,
                )
        if timezone.is_naive(nueva_fecha):
            nueva_fecha = make_aware(nueva_fecha)
    except ValueError as exc:
        return JsonResponse({'ok': False, 'error': f'Fecha inválida: {exc}'}, status=400)

    publicacion.fecha_publicacion = nueva_fecha
    publicacion.save(update_fields=['fecha_publicacion'])
    return JsonResponse({'ok': True, 'id': publicacion.pk, 'fecha': publicacion.fecha_publicacion.isoformat()})
