import re
import json
from pathlib import Path
from src.models.photo import GalleryMetadata


class PhotoMetadataService:
    def scan_processed_photos(self):
        prod_pics_dir = Path("prod/pics/full")
        if not prod_pics_dir.exists():
            return []
        
        photos = list(prod_pics_dir.glob("*.jpg"))
        # Sort by filename to maintain chronological order
        photos.sort(key=lambda p: p.name)
        return photos
    
    def extract_metadata_from_filename(self, filename):
        # Pattern: collection-YYYYMMDDTHHMMSS-camera-counter.jpg
        # Example: wedding-20250809T132034-r5a-0.jpg
        pattern = r"([^-]+)-(\d{8}T\d{6})-([^-]+)-([0-9A-V])\.jpg"
        match = re.match(pattern, filename)
        
        if not match:
            return {}
        
        return {
            "collection": match.group(1),
            "timestamp": match.group(2),
            "camera": match.group(3),
            "counter": match.group(4)
        }
    
    def generate_json_metadata(self):
        photos = self.scan_processed_photos()
        photo_data = []
        
        for photo_path in photos:
            filename = photo_path.name
            metadata = self.extract_metadata_from_filename(filename)
            
            if metadata:
                # Generate URLs for the photos
                base_name = filename.replace('.jpg', '')
                # Check if WebP thumbnail exists, otherwise fall back to JPEG
                webp_thumb = f"{base_name}.webp"
                thumb_path = Path("prod/pics/thumb") / webp_thumb
                if thumb_path.exists():
                    thumb_filename = webp_thumb
                else:
                    thumb_filename = filename
                    
                photo_data.append({
                    "filename": filename,
                    "timestamp": metadata["timestamp"],
                    "camera": metadata["camera"],
                    "counter": metadata["counter"],
                    "thumb_url": f"photos/thumb/{thumb_filename}",
                    "web_url": f"photos/web/{filename}",
                    "full_url": f"photos/full/{filename}"
                })
        
        return {"photos": photo_data}
    
    def generate_json_metadata_from_file(self, metadata_file_path: str) -> dict:
        """Generate frontend JSON metadata from gallery-metadata.json file.
        
        Args:
            metadata_file_path: Path to gallery-metadata.json file
            
        Returns:
            Dictionary with frontend-optimized photo data
        """
        with open(metadata_file_path, 'r') as f:
            metadata_dict = json.load(f)
        
        # Parse using dataclass
        gallery_metadata = GalleryMetadata.from_dict(metadata_dict)
        
        photo_data = []
        
        for photo in gallery_metadata.photos:
            # Combine camera make and model
            camera_parts = []
            if photo.exif.camera.get("make"):
                camera_parts.append(photo.exif.camera["make"])
            if photo.exif.camera.get("model"):
                camera_parts.append(photo.exif.camera["model"])
            camera_name = " ".join(camera_parts) if camera_parts else "Unknown"
            
            photo_data.append({
                "id": photo.id,
                "timestamp": photo.exif.corrected_timestamp,
                "camera": camera_name,
                "full_url": f"photos/{photo.files.full}",
                "web_url": f"photos/{photo.files.web}",
                "thumb_url": f"photos/thumb/{photo.files.thumb}"
            })
        
        return {"photos": photo_data}