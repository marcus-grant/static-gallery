import json
import shutil
from pathlib import Path


class StaticAssetService:
    def copy_css_files(self, source_dir, output_dir):
        source_path = Path(source_dir)
        output_path = Path(output_dir)
        
        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Copy CSS files
        copied_count = 0
        if source_path.exists():
            for css_file in source_path.glob("*.css"):
                shutil.copy2(str(css_file), str(output_path / css_file.name))
                copied_count += 1
        
        return {
            'success': True,
            'copied': copied_count
        }
    
    def copy_js_files(self, source_dir, output_dir):
        source_path = Path(source_dir)
        output_path = Path(output_dir)
        
        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Copy JS files
        copied_count = 0
        if source_path.exists():
            for js_file in source_path.glob("*.js"):
                shutil.copy2(str(js_file), str(output_path / js_file.name))
                copied_count += 1
        
        return {
            'success': True,
            'copied': copied_count
        }
    
    def generate_photos_json(self, photo_data, output_path):
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(photo_data, f, indent=2)
        
        return {'success': True}