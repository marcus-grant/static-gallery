from bs4 import BeautifulSoup
from src.services.template_renderer import TemplateRenderer


def test_photo_cell_component_renders_basic_structure():
    """Test that photo-cell component renders with basic thumbnail structure"""
    renderer = TemplateRenderer()
    
    # Mock photo data for a single photo (needs to be wrapped in photo object)
    photo_data = {
        "photo": {
            "filename": "2024-06-15_14-30-45_wedding-ceremony.jpg",
            "thumb_url": "photos/thumb/2024-06-15_14-30-45_wedding-ceremony.webp",
            "web_url": "photos/web/2024-06-15_14-30-45_wedding-ceremony.jpg"
        }
    }
    
    html = renderer.render("components/photo-cell.j2.html", photo_data)
    soup = BeautifulSoup(html, 'html.parser')
    
    # Check for clickable image element
    img = soup.find('img')
    assert img is not None
    assert photo_data["photo"]["thumb_url"] in img['src']
    
    # TODO: Add Alpine.js click handler test after JS implementation
    # clickable_element = soup.find(attrs={'@click': True})
    # assert clickable_element is not None


def test_photo_cell_component_has_proper_alt_text():
    """Test that photo-cell has accessible alt text"""
    renderer = TemplateRenderer()
    
    photo_data = {
        "photo": {
            "filename": "2024-06-15_14-30-45_wedding-ceremony.jpg",
            "thumb_url": "photos/thumb/2024-06-15_14-30-45_wedding-ceremony.webp",
            "web_url": "photos/web/2024-06-15_14-30-45_wedding-ceremony.jpg"
        }
    }
    
    html = renderer.render("components/photo-cell.j2.html", photo_data)
    soup = BeautifulSoup(html, 'html.parser')
    
    img = soup.find('img')
    assert img is not None
    assert 'alt' in img.attrs
    assert len(img['alt']) > 0


def test_photo_cell_component_includes_responsive_classes():
    """Test that photo-cell includes Tailwind responsive classes"""
    renderer = TemplateRenderer()
    
    photo_data = {
        "photo": {
            "filename": "2024-06-15_14-30-45_wedding-ceremony.jpg", 
            "thumb_url": "photos/thumb/2024-06-15_14-30-45_wedding-ceremony.webp",
            "web_url": "photos/web/2024-06-15_14-30-45_wedding-ceremony.jpg"
        }
    }
    
    html = renderer.render("components/photo-cell.j2.html", photo_data)
    soup = BeautifulSoup(html, 'html.parser')
    
    # Check for responsive container with Tailwind classes
    container = soup.find(class_=lambda x: x and any(cls in x for cls in ['aspect-square', 'cursor-pointer']))
    assert container is not None