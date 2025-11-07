import os


def asset_path(filename: str) -> str:
    """
    Devuelve la ruta absoluta de un recurso en la carpeta /assets
    para poder usar imágenes y archivos en cualquier vista.
    """
    base = os.path.join(os.path.dirname(__file__), "..", "assets")
    return os.path.abspath(os.path.join(base, filename))


