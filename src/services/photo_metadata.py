import re
from pathlib import Path


class PhotoMetadataService:
    def scan_processed_photos(self):
        prod_pics_dir = Path("prod/pics/full")
        if not prod_pics_dir.exists():
            return []
        
        photos = list(prod_pics_dir.glob("*.jpg"))
        return photos
    
    def extract_metadata_from_filename(self, filename):
        pattern = r"wedding-(\d{8}T\d{6}\.\d{3}Z[+-]\d{4})-([^-]+)-(\d{3})\.jpg"
        match = re.match(pattern, filename)
        
        if not match:
            return {}
        
        return {
            "timestamp": match.group(1),
            "camera": match.group(2),
            "sequence": match.group(3)
        }
    
    def generate_json_metadata(self):
        photos = self.scan_processed_photos()
        photo_data = []
        
        for photo_path in photos:
            filename = photo_path.name
            metadata = self.extract_metadata_from_filename(filename)
            
            if metadata:
                photo_data.append({
                    "filename": filename,
                    "timestamp": metadata["timestamp"],
                    "camera": metadata["camera"],
                    "sequence": metadata["sequence"]
                })
        
        return {"photos": photo_data}