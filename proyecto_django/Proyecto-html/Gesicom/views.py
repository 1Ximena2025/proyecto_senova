"""Vistas de la app 'Gesicom'.

Incluye:
- Páginas públicas (home, contacto, ayuda)
- Gestión y listas de envíos de evidencia
- Reportes y exportación CSV
- Control de acceso por grupos/roles
"""
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from .models import Envio
from .utils import (
    require_group, is_admin_or_group, apply_date_filters,
    calculate_stats, calculate_monthly_stats
)
from django.http import HttpResponse
import csv

from django.shortcuts import render

def editar_perfil(request):
    return render(request, 'editar_perfil/editar.html')

def index(request):
    # Mantener compatibilidad; usar home como contenido principal
    return render(request, 'home.html')


def home(request):
    is_basic = False
    if request.user.is_authenticated:
        is_basic = request.user.groups.filter(name='usuario').exists()
    return render(request, 'home.html', {'is_basic_user': is_basic})


@require_group('usuario')
def role_usuario(request):
    return render(request, 'home.html', {'is_basic_user': True})


def nosotros(request):
    return render(request, 'nosotros.html')


def contacto(request):
    return render(request, 'contacto.html')


def ayuda(request):
    return render(request, 'ayuda.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@require_group('instructor')
def role_instructor(request):
    return render(request, 'roles/instructor.html')


@require_group('investigador')
def role_investigador(request):
    return render(request, 'roles/investigador.html')


@require_group('dinamizador')
def role_dinamizador(request):
    return render(request, 'roles/dinamizador.html')


@require_group('coordinador')
def role_coordinador(request):
    return render(request, 'roles/coordinador.html')


def portal(request):
    # Redirige al selector de roles (home)
    return redirect('home')


def admin_menu(request):
    return render(request, 'admin/menu.html')

def proyecciones(request):
    """Muestra estadísticas generales de envíos."""
    consulta = Envio.objects.all()
    
    # Calcular estadísticas por tipo de evidencia
    estadisticas_categoria, total_envios = calculate_stats(consulta, 'tipo_evidencia')
    
    # Calcular estadísticas por proyecto
    estadisticas_proyecto, _ = calculate_stats(consulta, 'proyecto')
    
    # Reemplazar claves para coherencia con template
    estadisticas_categoria = [
        {'tipo_evidencia': s['field_value'], 'total': s['total'], 'porcentaje': s['porcentaje']}
        for s in estadisticas_categoria
    ]
    estadisticas_proyecto = [
        {'proyecto': s['field_value'], 'total': s['total'], 'porcentaje': s['porcentaje']}
        for s in estadisticas_proyecto
    ]

    context = {
        'total_envios': total_envios,
        'estadisticas_categoria': estadisticas_categoria,
        'estadisticas_proyecto': estadisticas_proyecto,
    }
    return render(request, 'admin/proyecciones.html', context)


def reportes(request):
    """Genera reportes filtrados de envíos."""
    proyecto = request.GET.get('proyecto', '')
    inicio = request.GET.get('start', '')
    fin = request.GET.get('end', '')

    consulta = Envio.objects.all()
    if proyecto:
        consulta = consulta.filter(proyecto=proyecto)
    
    consulta = apply_date_filters(consulta, inicio, fin)

    # Calcular estadísticas por categoría
    estadisticas_categoria, total_envios = calculate_stats(consulta, 'tipo_evidencia')
    estadisticas_categoria = [
        {'tipo_evidencia': s['field_value'], 'total': s['total'], 'porcentaje': s['porcentaje']}
        for s in estadisticas_categoria
    ]
    
    # Calcular estadísticas mensuales
    estadisticas_mensuales, _ = calculate_monthly_stats(consulta)

    opcion_proyectos = [p for p, _ in Envio.PROYECTO_CHOICES]

    context = {
        'proyecto': proyecto,
        'start': inicio,
        'end': fin,
        'opciones_proyectos': opcion_proyectos,
        'estadisticas_categoria': estadisticas_categoria,
        'estadisticas_mensuales': estadisticas_mensuales,
    }
    return render(request, 'admin/reportes.html', context)


def reportes_csv(request):
    """Exporta reportes filtrados en formato CSV."""
    proyecto = request.GET.get('proyecto', '')
    inicio = request.GET.get('start', '')
    fin = request.GET.get('end', '')

    consulta = Envio.objects.all()
    if proyecto:
        consulta = consulta.filter(proyecto=proyecto)
    
    consulta = apply_date_filters(consulta, inicio, fin)

    respuesta = HttpResponse(content_type='text/csv')
    respuesta['Content-Disposition'] = 'attachment; filename="reportes.csv"'
    escritor = csv.writer(respuesta)
    escritor.writerow(['fecha_envio', 'nombre', 'proyecto', 'tipo_evidencia', 'link_evidencia', 'observaciones'])
    for envio in consulta.order_by('fecha_envio'):
        escritor.writerow([
            envio.fecha_envio.isoformat() if envio.fecha_envio else '',
            envio.nombre,
            envio.proyecto,
            envio.tipo_evidencia,
            envio.link_evidencia or '',
            (envio.observaciones or '').replace('\r\n', ' ').replace('\n', ' '),
        ])
    return respuesta


@login_required
def evidencia(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        proyecto = request.POST.get('proyecto', '').strip()
        tipos = request.POST.getlist('evidencias')
        tipo_evidencia = ', '.join(tipos) if tipos else 'Sin especificar'
        enlace = request.POST.get('linkArchivo', '').strip()
        archivo = request.FILES.get('archivo')
        observaciones = request.POST.get('observaciones', '').strip()

        errores = []

        # Validaciones
        if not (enlace or archivo):
            errores.append('Debe proporcionar un enlace o adjuntar un archivo (al menos uno).')
        if not nombre:
            errores.append('El nombre es obligatorio.')
        if not proyecto:
            errores.append('Debe seleccionar el proyecto.')

        # Validar tamaño de archivo (máximo 10MB)
        if archivo and archivo.size > 10 * 1024 * 1024:
            errores.append('El archivo es demasiado grande. Tamaño máximo: 10MB.')

        # Validar tipos de archivo permitidos
        if archivo:
            extensiones_permitidas = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                                     '.txt', '.jpg', '.jpeg', '.png', '.zip', '.rar']
            nombre_archivo = archivo.name.lower()
            if not any(nombre_archivo.endswith(ext) for ext in extensiones_permitidas):
                errores.append(f'Tipo de archivo no permitido. Extensiones permitidas: {", ".join(extensiones_permitidas)}')

        if errores:
            return render(request, 'formulario.html', {
                'errores': errores,
                'exito': False,
                'nombre': nombre,
                'proyecto': proyecto,
                'tipos': tipos,
                'enlace_archivo': enlace,
                'observaciones': observaciones,
            })

        # Crear el envío
        envio = Envio(
            usuario=request.user,
            nombre=nombre,
            proyecto=proyecto,
            tipo_evidencia=tipo_evidencia,
            link_evidencia=enlace if enlace else None,
            archivo_evidencia=archivo,
            observaciones=observaciones,
        )
        envio.save()

        # Mensaje de éxito con información del archivo
        mensaje_exito = 'Evidencia enviada correctamente'
        if archivo:
            mensaje_exito += f'. Archivo guardado: {envio.archivo_evidencia.name}'

        return render(request, 'formulario.html', {
            'exito': True,
            'mensaje_exito': mensaje_exito
        })

    return render(request, 'formulario.html')


@login_required
def evidencias_list(request):
    """Lista de envíos con filtros, búsqueda y paginación."""
    consulta = Envio.objects.select_related('usuario').all()

    # Filtro por proyecto
    proyecto = request.GET.get('proyecto', '')
    if proyecto:
        consulta = consulta.filter(proyecto=proyecto)

    # Búsqueda por nombre, tipo y observaciones
    termino_busqueda = (request.GET.get('q') or '').strip()
    if termino_busqueda:
        consulta = consulta.filter(
            Q(nombre__icontains=termino_busqueda) |
            Q(tipo_evidencia__icontains=termino_busqueda) |
            Q(observaciones__icontains=termino_busqueda)
        )

    # Ordenamiento
    orden = request.GET.get('order', 'fecha_envio')
    direccion = request.GET.get('dir', 'desc')
    permitidos = {'fecha_envio', 'nombre', 'proyecto', 'tipo_evidencia'}
    if orden in permitidos:
        criterio_orden = orden if direccion == 'asc' else f'-{orden}'
        consulta = consulta.order_by(criterio_orden)
    else:
        consulta = consulta.order_by('-fecha_envio')

    # Paginación (tamaño fijo)
    paginador = Paginator(consulta, 10)
    numero_pagina = request.GET.get('page')
    objeto_pagina = paginador.get_page(numero_pagina)

    context = {
        'envios': objeto_pagina,
        'proyecto': proyecto,
        'order': orden,
        'dir': direccion,
    }
    return render(request, 'evidencias_list.html', context)


def instructor_table(request):
    """Vista para mostrar tabla de instructores."""
    return render(request, 'instructor_table.html')


def access_denied(request):
    """Vista para mostrar página de acceso denegado."""
    return render(request, 'access_denied.html')

def exportar_csv(request):
    """Exportar envíos a CSV."""
    consulta = Envio.objects.select_related('usuario').all().order_by('-fecha_envio')

    respuesta = HttpResponse(content_type='text/csv')
    respuesta['Content-Disposition'] = 'attachment; filename="envios.csv"'
    escritor = csv.writer(respuesta)
    escritor.writerow(['fecha_envio', 'nombre', 'proyecto', 'tipo_evidencia', 'link_evidencia', 'observaciones'])
    for envio in consulta:
        escritor.writerow([
            envio.fecha_envio.isoformat() if envio.fecha_envio else '',
            envio.nombre,
            envio.proyecto,
            envio.tipo_evidencia,
            envio.link_evidencia or '',
            (envio.observaciones or '').replace('\r\n', ' ').replace('\n', ' '),
        ])
    return respuesta



