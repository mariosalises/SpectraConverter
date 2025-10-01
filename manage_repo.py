import os
import shutil
import tarfile
from tufup.repo import Repository
from version import __version__

APP_NAME = 'SpectraConverter'
REPO_DIR = 'repo'
BUNDLE_DIR = 'dist'

# Crear instancia de repositorio
repo = Repository(app_name=APP_NAME, repo_dir=REPO_DIR)

# Inicializar si no existe
if not os.path.exists(REPO_DIR):
    print(f'Inicializando repositorio en "{REPO_DIR}"...')
    repo.initialize()
    print('Repositorio inicializado correctamente.')

    # Copiar root.json a assets
    metadata_src = os.path.join(REPO_DIR, 'metadata', 'root.json')
    metadata_dst_dir = os.path.join('assets', 'metadata')
    os.makedirs(metadata_dst_dir, exist_ok=True)
    shutil.copy(metadata_src, os.path.join(metadata_dst_dir, 'root.json'))
    print(f'Se ha copiado "root.json" a "{metadata_dst_dir}".')
else:
    print(f'El repositorio en "{REPO_DIR}" ya existe.')

# Comprobar ejecutable
bundle_path = os.path.join(BUNDLE_DIR, f'{APP_NAME}.exe')
if not os.path.exists(bundle_path):
    print(f'No se encontró el ejecutable en "{BUNDLE_DIR}".')
    exit(1)

# Preparar carpeta targets
targets_dir = os.path.join(REPO_DIR, 'targets')
os.makedirs(targets_dir, exist_ok=True)

# Eliminar versión existente si hay conflicto
old_archive = os.path.join(targets_dir, f'{APP_NAME}-{__version__}.tar.gz')
if os.path.exists(old_archive):
    print(f'Eliminando archivo existente: {old_archive}')
    os.remove(old_archive)

# Si no hay archivos previos, creamos un .tar.gz temporal para inicializar roles
if not os.listdir(targets_dir):
    temp_tar = os.path.join(targets_dir, f'{APP_NAME}-{__version__}.tar.gz')
    with tarfile.open(temp_tar, "w:gz") as tar:
        tar.add(bundle_path, arcname=os.path.basename(bundle_path))
    print(f'Archivo temporal creado en "{temp_tar}" para inicializar el repositorio.')

# Añadir bundle real
print(f'Agregando versión "{__version__}" desde "{BUNDLE_DIR}"...')
repo.add_bundle(new_version=__version__, new_bundle_dir=BUNDLE_DIR)

# Publicar cambios
print(f'Firmando metadatos con las claves en: "{repo.keys_dir}"')
repo.publish_changes(private_key_dirs=[repo.keys_dir])
print(f'Versión {__version__} añadida y publicada en el repositorio local.')
print(f'Copia el contenido de "{os.path.join(REPO_DIR, "repository")}" a tu release de GitHub.')
