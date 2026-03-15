import subprocess
import os
import glob

# Ruta al manage.py y carpeta de fixtures
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MANAGE_PY = os.path.join(BASE_DIR, 'manage.py')
FIXTURES_DIR = os.path.join(BASE_DIR, 'fixtures')

# Buscar el respaldo más reciente
backups = sorted(glob.glob(os.path.join(FIXTURES_DIR, 'users_backup_*.json')))
if not backups:
    print("No se encontró ningún respaldo de usuarios.")
    exit(1)

backup_file = backups[-1]
print(f"Restaurando usuarios desde: {backup_file}")

# Comando para restaurar usuarios
cmd = f'python {MANAGE_PY} loaddata "{backup_file}"'
res = subprocess.run(cmd, shell=True)
if res.returncode == 0:
    print("Restauración exitosa.")
else:
    print("Error al restaurar usuarios.")
