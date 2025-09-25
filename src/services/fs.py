import settings
from pathlib import Path


def ls_full():
    path = Path(settings.PIC_SOURCE_PATH_FULL)
    if not path.exists():
        return []
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    result = []
    
    for file_path in path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            result.append(file_path)
    
    return result