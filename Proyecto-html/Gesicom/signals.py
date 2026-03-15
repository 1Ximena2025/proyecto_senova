"""Señales (signals) para gestionar grupos y asignaciones automáticas.

- `ensure_groups`: crea los grupos necesarios tras aplicar migraciones.
- `assign_default_group`: al crear un usuario, se le asigna el grupo 'usuario' por defecto.
"""
from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import User, Group


@receiver(post_migrate)
def ensure_groups(sender, **kwargs):
    """Crea grupos de rol si no existen (se ejecuta tras `migrate`)."""
    for name in ["usuario", "instructor", "investigador", "dinamizador", "coordinador", "administrador"]:
        Group.objects.get_or_create(name=name)


@receiver(post_save, sender=User)
def assign_default_group(sender, instance, created, **kwargs):
    """Al crear un usuario nuevo, añadirlo al grupo 'usuario' por defecto."""
    if created:
        group, _ = Group.objects.get_or_create(name="usuario")
        instance.groups.add(group)
