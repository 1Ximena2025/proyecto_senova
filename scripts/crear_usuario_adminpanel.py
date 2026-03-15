from django.contrib.auth.models import User

USERNAME = 'adminpanel'
EMAIL = 'adminpanel@example.com'
PASSWORD = 'admin1234'

u, created = User.objects.get_or_create(username=USERNAME, defaults={
    'email': EMAIL,
    'first_name': 'Admin',
    'last_name': 'Panel',
})
if created:
    u.set_password(PASSWORD)
    u.is_staff = True
    u.save()
    print(f'Usuario creado: {USERNAME} / {PASSWORD}')
else:
    print(f'El usuario ya existe. Password: {PASSWORD}')
