"""
Management command para poblar la base de datos con datos de prueba.

Uso:
    python manage.py seed_data
    python manage.py seed_data --flush   # borra datos previos antes de insertar
"""

from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from contenido.models import Campana, Canal, Publicacion
from cuentas.models import PerfilUsuario


class Command(BaseCommand):
    help = 'Carga datos de prueba: canales, campañas, publicaciones y usuario admin.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Elimina todos los datos previos antes de insertar.',
        )

    def handle(self, *args, **options):
        if options['flush']:
            self.stdout.write('  Borrando datos previos...')
            Publicacion.objects.all().delete()
            Campana.objects.all().delete()
            Canal.objects.all().delete()
            self.stdout.write(self.style.WARNING('  Datos previos eliminados.'))

        # ── 1. Superusuario ───────────────────────────────────────────────────
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email':      'admin@socialplan.com',
                'first_name': 'Admin',
                'last_name':  'SocialPlan',
                'is_staff':   True,
                'is_superuser': True,
            },
        )
        if created:
            admin.set_password('admin1234')
            admin.save()
            self.stdout.write(self.style.SUCCESS('  Usuario admin creado (admin / admin1234)'))
        else:
            self.stdout.write('  Usuario admin ya existe.')

        # Usuarios de prueba adicionales
        roles_usuarios = [
            ('redactor1',  'redactor',  'Ana',    'García'),
            ('disenador1', 'disenador', 'Carlos', 'López'),
            ('manager1',   'aprobador', 'Laura',  'Martínez'),
        ]
        usuarios = [admin]
        for uname, rol, fname, lname in roles_usuarios:
            u, c = User.objects.get_or_create(
                username=uname,
                defaults={'first_name': fname, 'last_name': lname,
                          'email': f'{uname}@socialplan.com'},
            )
            if c:
                u.set_password('test1234')
                u.save()
                PerfilUsuario.objects.get_or_create(usuario=u, defaults={'rol': rol})
                self.stdout.write(f'  Usuario {uname} creado ({uname} / test1234)')
            usuarios.append(u)

        # ── 2. Canales ────────────────────────────────────────────────────────
        canales_data = [
            ('Instagram',  'fab fa-instagram'),
            ('YouTube',    'fab fa-youtube'),
            ('Blog',       'bx bx-globe'),
            ('LinkedIn',   'fab fa-linkedin'),
            ('TikTok',     'fab fa-tiktok'),
            ('Newsletter', 'bx bx-envelope'),
        ]
        canales = {}
        for nombre, icono in canales_data:
            canal, _ = Canal.objects.get_or_create(
                nombre=nombre, defaults={'icono': icono}
            )
            canales[nombre] = canal
        self.stdout.write(f'  {len(canales)} canales listos.')

        # ── 3. Campañas ───────────────────────────────────────────────────────
        hoy = timezone.now().date()
        campanas_data = [
            ('Lanzamiento Q3 2026',  'Campaña de lanzamiento del tercer trimestre.',
             hoy - timedelta(days=30), hoy + timedelta(days=30), True),
            ('Campaña Verano 2026',  'Contenido de temporada estival para todas las redes.',
             hoy - timedelta(days=60), hoy + timedelta(days=10), True),
            ('Black Friday 2026',    'Preparación y publicación para el evento de descuentos.',
             hoy + timedelta(days=90), hoy + timedelta(days=120), True),
            ('Campaña Q1 2026',      'Campaña ya finalizada del primer trimestre.',
             hoy - timedelta(days=180), hoy - timedelta(days=90), False),
        ]
        campanas = []
        for nombre, desc, inicio, fin, activa in campanas_data:
            c, _ = Campana.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'descripcion': desc,
                    'fecha_inicio': inicio,
                    'fecha_fin':    fin,
                    'activa':       activa,
                },
            )
            campanas.append(c)
        self.stdout.write(f'  {len(campanas)} campañas listas.')

        # ── 4. Publicaciones ──────────────────────────────────────────────────
        import random
        random.seed(42)

        ahora = timezone.now()
        estados = ['borrador', 'revision', 'aprobado', 'publicado']

        titulos = [
            'Cómo crear contenido viral en Instagram',
            '5 tendencias de redes sociales para 2026',
            'Tutorial: Edición de video para Reels',
            'Guía definitiva de LinkedIn para empresas',
            'SEO en 2026: lo que debes saber',
            'Detrás de escena: nuestro proceso creativo',
            'Lanzamiento de nueva colección — sneak peek',
            'Por qué el video corto domina el contenido',
            'Newsletter mensual: resumen de julio',
            'TikTok vs Instagram: ¿dónde publicar?',
            'Cómo escribir captions que conviertan',
            'Estrategia de contenido para el Q4',
            'Caso de éxito: campaña de verano 2025',
            'Herramientas para diseñar posts sin ser diseñador',
            'El poder del storytelling en redes sociales',
            'Cómo medir el engagement de tu comunidad',
            'Guía de hashtags para Instagram 2026',
            'Blog post: tendencias de marketing digital',
            'YouTube Shorts: guía para principiantes',
            'Automatización de publicaciones: pros y contras',
        ]

        canal_list  = list(canales.values())
        redactores  = usuarios[:3]

        publicaciones_creadas = 0
        for i, titulo in enumerate(titulos):
            canal   = canal_list[i % len(canal_list)]
            estado  = estados[i % len(estados)]
            campana = campanas[i % len(campanas)] if i % 3 != 0 else None
            redactor   = redactores[i % len(redactores)]
            disenador  = redactores[(i + 1) % len(redactores)]

            # Distribuir en el tiempo: pasado, presente y futuro
            delta_days = (i - 10) * 3   # de -30 a +30 días aprox
            fecha = ahora + timedelta(days=delta_days, hours=random.randint(8, 20))

            _, created = Publicacion.objects.get_or_create(
                titulo=titulo,
                defaults={
                    'contenido':        f'Contenido de prueba para "{titulo}". '
                                        f'Este es el cuerpo del post que se publicará en {canal.nombre}.',
                    'fecha_publicacion': fecha,
                    'estado':           estado,
                    'canal':            canal,
                    'campana':          campana,
                    'redactor':         redactor,
                    'disenador':        disenador,
                    'engagement_rate':  round(random.uniform(1.5, 8.5), 2),
                    'clics':            random.randint(50, 2000),
                },
            )
            if created:
                publicaciones_creadas += 1

        self.stdout.write(f'  {publicaciones_creadas} publicaciones creadas.')

        # ── Resumen final ─────────────────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('╔══════════════════════════════════════╗'))
        self.stdout.write(self.style.SUCCESS('║  ✅  Datos de prueba cargados         ║'))
        self.stdout.write(self.style.SUCCESS('╠══════════════════════════════════════╣'))
        self.stdout.write(self.style.SUCCESS(f'║  Canales:       {Canal.objects.count():<22}║'))
        self.stdout.write(self.style.SUCCESS(f'║  Campañas:      {Campana.objects.count():<22}║'))
        self.stdout.write(self.style.SUCCESS(f'║  Publicaciones: {Publicacion.objects.count():<22}║'))
        self.stdout.write(self.style.SUCCESS('╠══════════════════════════════════════╣'))
        self.stdout.write(self.style.SUCCESS('║  Acceso:  http://127.0.0.1:8000/     ║'))
        self.stdout.write(self.style.SUCCESS('║  Usuario: admin  Clave: admin1234    ║'))
        self.stdout.write(self.style.SUCCESS('╚══════════════════════════════════════╝'))
