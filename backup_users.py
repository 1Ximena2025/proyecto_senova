import subprocess
import os
from datetime import datetime

# Ruta al manage.py y carpeta de fixtures
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MANAGE_PY = os.path.join(BASE_DIR, 'manage.py')
FIXTURES_DIR = os.path.join(BASE_DIR, 'fixtures')

# Nombre del archivo de respaldo (con fecha)
fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_file = os.path.join(FIXTURES_DIR, f'users_backup_{fecha}.json')

# Comando para exportar usuarios
cmd = f'python {MANAGE_PY} dumpdata auth.user > "{backup_file}"'

print(f"Respaldando usuarios en: {backup_file}")
res = subprocess.run(cmd, shell=True)
if res.returncode == 0:
    print("Respaldo exitoso.")
else:
    print("Error al respaldar usuarios.")
