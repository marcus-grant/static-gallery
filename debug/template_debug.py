"""
Template debugging utilities for development and testing
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.services.template_renderer import TemplateRenderer
from bs4 import BeautifulSoup
import json


class TemplateDebugger:
    def __init__(self):
        self.renderer = TemplateRenderer()
    
    def render_and_print(self, template_method, data, title="Template Output"):
        """Render a template and print formatted output"""
        print(f"\n{'='*60}")
        print(f"{title}")
        print(f"{'='*60}")
        
        html = template_method(data)
        print("RAW HTML:")
        print("-" * 40)
        print(html)
        
        print("\nPARSED STRUCTURE:")
        print("-" * 40)
        soup = BeautifulSoup(html, 'html.parser')
        print(soup.prettify())
        
        print(f"\n{'='*60}\n")
        return html
    
    def debug_gallery(self, photo_count=2):
        """Debug gallery template with sample photos"""
        sample_photos = []
        for i in range(photo_count):
            sample_photos.append({
                "filename": f"2024-06-15_14-{30+i*2:02d}-{45+i*5:02d}_wedding-sample-{i+1}.jpg",
                "thumb_url": f"/photos/thumb/2024-06-15_14-{30+i*2:02d}-{45+i*5:02d}_wedding-sample-{i+1}.webp",
                "web_url": f"/photos/web/2024-06-15_14-{30+i*2:02d}-{45+i*5:02d}_wedding-sample-{i+1}.jpg"
            })
        
        data = {"photos": sample_photos}
        return self.render_and_print(
            self.renderer.render_gallery, 
            data, 
            f"Gallery Template with {photo_count} Photos"
        )
    
    def debug_photo_cell(self):
        """Debug single photo-cell component"""
        data = {
            "photo": {
                "filename": "2024-06-15_14-30-45_wedding-ceremony.jpg",
                "thumb_url": "/photos/thumb/2024-06-15_14-30-45_wedding-ceremony.webp",
                "web_url": "/photos/web/2024-06-15_14-30-45_wedding-ceremony.jpg"
            }
        }
        return self.render_and_print(
            self.renderer.render_photo_cell,
            data,
            "Photo Cell Component"
        )
    
    def analyze_template_structure(self, html):
        """Analyze and report on template structure"""
        soup = BeautifulSoup(html, 'html.parser')
        
        analysis = {
            "total_elements": len(soup.find_all()),
            "images": len(soup.find_all('img')),
            "clickable_elements": len(soup.find_all(attrs={'@click': True})),
            "alpine_data_elements": len(soup.find_all(attrs={'x-data': True})),
            "grid_containers": len(soup.find_all(class_=lambda x: x and 'grid' in x)),
            "responsive_classes": []
        }
        
        # Check for responsive classes
        for element in soup.find_all(class_=True):
            classes = element.get('class', [])
            responsive = [cls for cls in classes if any(prefix in cls for prefix in ['sm:', 'md:', 'lg:', 'xl:'])]
            if responsive:
                analysis["responsive_classes"].extend(responsive)
        
        analysis["responsive_classes"] = list(set(analysis["responsive_classes"]))
        
        print("\nTEMPLATE ANALYSIS:")
        print("-" * 40)
        print(json.dumps(analysis, indent=2))
        
        return analysis


# Convenience functions for quick debugging
def debug_gallery(photo_count=2):
    """Quick gallery debug"""
    debugger = TemplateDebugger()
    return debugger.debug_gallery(photo_count)

def debug_photo_cell():
    """Quick photo-cell debug"""
    debugger = TemplateDebugger()
    return debugger.debug_photo_cell()

def analyze_html(html):
    """Quick HTML analysis"""
    debugger = TemplateDebugger()
    return debugger.analyze_template_structure(html)


if __name__ == "__main__":
    # Example usage
    print("Template Debugging Examples")
    
    # Debug gallery with 3 photos
    debug_gallery(3)
    
    # Debug individual photo cell
    debug_photo_cell()