from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

@receiver(pre_delete, sender=User)
def proteger_borrado_usuario(sender, instance, using, **kwargs):
    # Solo permitir el borrado si es superusuario y lo hace desde el admin
    # (o puedes personalizar la lógica según tus necesidades)
    raise PermissionDenied("El borrado de usuarios está deshabilitado para proteger la integridad del sistema. Si necesitas eliminar un usuario, contacta al administrador.")
