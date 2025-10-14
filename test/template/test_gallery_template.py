from bs4 import BeautifulSoup
from src.services.template_renderer import TemplateRenderer


def test_gallery_template_has_basic_structure():
    """Test that gallery template contains expected HTML structure"""
    renderer = TemplateRenderer()
    photo_data = {"photos": []}
    
    html = renderer.render("gallery.j2.html", photo_data)
    soup = BeautifulSoup(html, 'html.parser')
    
    # Check for required meta tags
    assert soup.find('meta', {'name': 'robots', 'content': 'noindex, nofollow'})
    assert soup.find('meta', {'name': 'viewport'})
    
    # Check for Alpine.js data attribute
    assert soup.find(attrs={'x-data': True})
    
    # Check for photo grid container
    assert soup.find(class_='grid')


def test_gallery_template_renders_photo_cells_when_photos_provided():
    """Test that gallery template includes photo-cell components for each photo"""
    renderer = TemplateRenderer()
    photo_data = {
        "photos": [
            {
                "filename": "2024-06-15_14-30-45_wedding-ceremony.jpg",
                "thumb_url": "/photos/thumb/2024-06-15_14-30-45_wedding-ceremony.webp",
                "web_url": "/photos/web/2024-06-15_14-30-45_wedding-ceremony.jpg"
            },
            {
                "filename": "2024-06-15_14-32-10_wedding-rings.jpg", 
                "thumb_url": "/photos/thumb/2024-06-15_14-32-10_wedding-rings.webp",
                "web_url": "/photos/web/2024-06-15_14-32-10_wedding-rings.jpg"
            }
        ]
    }
    
    html = renderer.render("gallery.j2.html", photo_data)
    soup = BeautifulSoup(html, 'html.parser')
    
    # Check that photo-cell components are rendered (images with click handlers)
    clickable_images = soup.find_all('img', src=lambda x: x and 'thumb' in x)
    assert len(clickable_images) == 2
    
    # Check for Alpine.js click handlers on photo cells
    click_elements = soup.find_all(attrs={'@click': True})
    assert len(click_elements) >= 2