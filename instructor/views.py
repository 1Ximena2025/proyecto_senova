from django.contrib.auth.decorators import login_required


from Gesicom.models import Envio
from Gesicom.utils import calculate_stats, calculate_monthly_stats, apply_date_filters
from django.db.models import Count, Q
import datetime

# Vista para el panel de reportes del instructor
@login_required(login_url='login')
def reportes_panel(request):
	# Filtros
	inicio = request.GET.get('inicio')
	fin = request.GET.get('fin')
	categoria = request.GET.get('categoria')
	consulta = Envio.objects.all()
	if inicio:
		consulta = consulta.filter(fecha_envio__gte=inicio)
	if fin:
		consulta = consulta.filter(fecha_envio__lte=fin)
	if categoria and categoria != 'Todas':
		consulta = consulta.filter(proyecto=categoria)

	# KPIs
	total_evidencias = consulta.count()
	nuevas_evidencias = consulta.filter(fecha_envio__gte=(datetime.date.today() - datetime.timedelta(days=30))).count()
	evidencias_aprobadas = consulta.filter(aprobada=True).count()
	evidencias_rechazadas = consulta.filter(rechazada=True).count()

	# Gráfica: Evidencias por día (últimos 12 días)
	hoy = datetime.date.today()
	dias = [(hoy - datetime.timedelta(days=i)) for i in range(11, -1, -1)]
	labels_dias = [d.strftime('%d/%m') for d in dias]
	nuevas_por_dia = [consulta.filter(fecha_envio=d).count() for d in dias]
	aprobadas_por_dia = [consulta.filter(fecha_envio=d, aprobada=True).count() for d in dias]

	# Gráfica: Categorías de evidencia
	stats_categoria, _ = calculate_stats(consulta, 'proyecto')
	labels_categoria = [s['field_value'] for s in stats_categoria]
	data_categoria = [s['total'] for s in stats_categoria]

	# Gráfica: Estado de evidencia
	data_estado = [evidencias_aprobadas, nuevas_evidencias, evidencias_rechazadas]

	# Gráfica: Evidencias por usuario (top 5)
	usuarios_stats = consulta.values('usuario__first_name', 'usuario__last_name').annotate(total=Count('id')).order_by('-total')[:5]
	labels_usuarios = [f"{u['usuario__first_name']} {u['usuario__last_name']}".strip() for u in usuarios_stats]
	data_usuarios = [u['total'] for u in usuarios_stats]

	# Opciones de categorías
	opciones_categorias = list(Envio.PROYECTO_CHOICES)

	context = {
		'total_evidencias': total_evidencias,
		'nuevas_evidencias': nuevas_evidencias,
		'evidencias_aprobadas': evidencias_aprobadas,
		'evidencias_rechazadas': evidencias_rechazadas,
		'labels_dias': labels_dias,
		'nuevas_por_dia': nuevas_por_dia,
		'aprobadas_por_dia': aprobadas_por_dia,
		'labels_categoria': labels_categoria,
		'data_categoria': data_categoria,
		'data_estado': data_estado,
		'labels_usuarios': labels_usuarios,
		'data_usuarios': data_usuarios,
		'opciones_categorias': opciones_categorias,
		'filtros': {
			'inicio': inicio or '',
			'fin': fin or '',
			'categoria': categoria or 'Todas',
		}
	}
	return render(request, 'reportes_panel.html', context)
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import re
from django.contrib.auth.models import User, Group
import logging
import traceback
from django.db import transaction, IntegrityError

logger = logging.getLogger(__name__)


ROLE_ROUTES = {
    'instructor': 'role_instructor',
    'investigador': 'role_investigador',
    'dinamizador': 'role_dinamizador',
    'coordinador': 'role_coordinador',
    'usuario': 'usuario',
}


def _validar_contraseña(contraseña1, contraseña2=None):
	errores = []

	if not contraseña1:
		errores.append('La contraseña es obligatoria.')
		return errores

	if contraseña2 and contraseña1 != contraseña2:
		errores.append('Las contraseñas no coinciden.')
		return errores

	if len(contraseña1) != 8:
		errores.append('La contraseña debe tener exactamente 8 caracteres.')

	tiene_mayuscula = re.search(r'[A-Z]', contraseña1) is not None
	tiene_digito = re.search(r'\d', contraseña1) is not None
	tiene_especial = re.search(r'[!@#$%^&*(),.?":{}|<>]', contraseña1) is not None

	if not tiene_mayuscula:
		errores.append('Debe contener al menos una letra mayúscula.')

	if not (tiene_digito or tiene_especial):
		errores.append('Debe contener al menos un número o carácter especial.')

	return errores


def login_view(request):
	rol = request.GET.get('role') or request.POST.get('role') or ''
	if rol not in ROLE_ROUTES:
		rol = ''

	success_msg = None
	if request.method == 'GET' and request.GET.get('created'):
		success_msg = 'Cuenta creada correctamente. Por favor inicia sesión.'

	if request.method == 'POST':
		entrada_usuario = (request.POST.get('username', '') or '').strip()
		contraseña = request.POST.get('password', '')
		recordar = request.POST.get('remember')

		usuario_para_auth = entrada_usuario
		if '@' in entrada_usuario and not User.objects.filter(username=entrada_usuario).exists():
			try:
				u = User.objects.get(email__iexact=entrada_usuario)
				usuario_para_auth = u.username
			except User.DoesNotExist:
				pass

		usuario = authenticate(request, username=usuario_para_auth, password=contraseña)
		if usuario is not None:
			login(request, usuario)
			if recordar:
				request.session.set_expiry(60 * 60 * 24 * 14)
			else:
				request.session.set_expiry(0)
			
			grupos_usuario = set(usuario.groups.values_list('name', flat=True))

			# 1. Si es Superusuario o está en el grupo 'administrador' -> Panel de Admin
			if usuario.is_superuser or 'administrador' in grupos_usuario:
				return redirect('admin_personalizado:dashboard')

			# 2. Si está en el grupo 'instructor' -> Panel de Instructor
			if 'instructor' in grupos_usuario:
				return redirect('role_instructor')

			# 3. Si el rol viene por URL/POST y coincide con un grupo del usuario -> Redirigir a ese rol
			if rol and rol in ROLE_ROUTES and rol in grupos_usuario:
				return redirect(ROLE_ROUTES[rol])

			# 4. Redirección por defecto basada en grupos prioritarios
			if 'investigador' in grupos_usuario: return redirect('role_investigador')
			if 'dinamizador' in grupos_usuario: return redirect('role_dinamizador')
			if 'coordinador' in grupos_usuario: return redirect('role_coordinador')
			
			destino = 'usuario' if 'usuario' in grupos_usuario else 'home'
			return redirect(destino)

		return render(request, 'login.html', {
			'error': 'Usuario o contraseña incorrectos',
			'role': rol,
			'username': entrada_usuario,
		})

	context = {'role': rol}
	if success_msg:
		context['success'] = success_msg
	return render(request, 'login.html', context)


def register_view(request):
	rol = request.GET.get('role') or request.POST.get('role') or ''
	if request.method == 'POST':
		try:
			logger.debug('register_view POST data: %s', dict(request.POST))
		except Exception:
			logger.exception('No se pudo serializar request.POST')
		nombre_usuario = (request.POST.get('username', '') or '').strip()
		correo = (request.POST.get('email', '') or '').strip().lower()
		contraseña1 = request.POST.get('password1', '')
		contraseña2 = request.POST.get('password2', '')

		errores = []
		if not nombre_usuario:
			errores.append('El usuario es obligatorio.')
		if not correo:
			errores.append('El correo es obligatorio.')

		errores.extend(_validar_contraseña(contraseña1, contraseña2))

		if User.objects.filter(username=nombre_usuario).exists():
			errores.append('Ese usuario ya existe. Prueba con otro.')

		if User.objects.filter(email=correo).exists():
			errores.append('Ese correo ya está registrado.')

		if errores:
			return render(request, 'register.html', {
				'errores': errores,
				'rol': rol,
				'nombre_usuario': nombre_usuario,
				'correo': correo,
			})

		try:
			with transaction.atomic():
				usuario = User.objects.create_user(username=nombre_usuario, email=correo, password=contraseña1)
				g, _ = Group.objects.get_or_create(name='usuario')
				usuario.groups.add(g)
				usuario.save()
				logger.info('Usuario creado desde register_view: %s (pk=%s)', usuario.username, getattr(usuario, 'pk', None))
				return redirect('/login/?created=1')
		except IntegrityError:
			errores.append('El usuario o correo ya existe.')
			return render(request, 'register.html', {
				'errores': errores,
				'rol': rol,
				'nombre_usuario': nombre_usuario,
				'correo': correo,
			})
		except Exception:
			tb = traceback.format_exc()
			logger.exception('Error creando usuario')
			errores.append('Error interno al crear la cuenta. Contacta al administrador.')
			return render(request, 'register.html', {
				'errores': errores,
				'rol': rol,
				'nombre_usuario': nombre_usuario,
				'correo': correo,
				'rastreo_debug': tb,
			})

	return render(request, 'register.html', {'rol': rol})


@login_required(login_url='login')
def panel_usuario(request):
    """Vista del panel personal del usuario."""
    return render(request, 'usuario/panel_usuario.html')


@login_required(login_url='login')
def panel_instructor(request):
    """Vista del panel personal del instructor."""
    return render(request, 'panel_instructor.html')


def logout_view(request):
    """Cerrar sesión del usuario."""
    logout(request)
    return redirect('login')