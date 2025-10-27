from bs4 import BeautifulSoup
from src.services.template_renderer import TemplateRenderer


def test_photo_grid_component_renders_container():
    """Test that photo-grid component renders a container div"""
    renderer = TemplateRenderer()
    
    context = {
        "photos": [],
        "grid_classes": "grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 p-4"
    }
    
    html = renderer.render("components/photo-grid.j2.html", context)
    soup = BeautifulSoup(html, 'html.parser')
    
    # Check for grid container
    grid_container = soup.find('div', class_=lambda x: x and 'grid' in x)
    assert grid_container is not None
    
    # Check that it has responsive classes
    classes = grid_container.get('class', [])
    assert any('grid-cols' in cls for cls in classes)


def test_photo_grid_component_renders_photo_cells():
    """Test that photo-grid includes photo-cell components for each photo"""
    renderer = TemplateRenderer()
    
    context = {
        "photos": [
            {
                "filename": "2024-06-15_14-30-45_photo1.jpg",
                "thumb_url": "photos/thumb/2024-06-15_14-30-45_photo1.webp",
                "web_url": "photos/web/2024-06-15_14-30-45_photo1.jpg"
            },
            {
                "filename": "2024-06-15_14-35-20_photo2.jpg", 
                "thumb_url": "photos/thumb/2024-06-15_14-35-20_photo2.webp",
                "web_url": "photos/web/2024-06-15_14-35-20_photo2.jpg"
            }
        ],
        "grid_classes": "grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 p-4"
    }
    
    html = renderer.render("components/photo-grid.j2.html", context)
    soup = BeautifulSoup(html, 'html.parser')
    
    # Check that photo cells are rendered (looking for anchor tags from photo-cell template)
    photo_links = soup.find_all('a', class_=lambda x: x and 'aspect-square' in x)
    assert len(photo_links) == 2
    
    # Check that images have correct src
    images = soup.find_all('img')
    assert len(images) == 2
    assert any('photo1.webp' in img.get('src', '') for img in images)
    assert any('photo2.webp' in img.get('src', '') for img in images)


def test_photo_grid_component_is_configurable():
    """Test that photo-grid accepts custom CSS classes"""
    renderer = TemplateRenderer()
    
    custom_classes = "grid grid-cols-3 gap-2 p-2"
    context = {
        "photos": [],
        "grid_classes": custom_classes
    }
    
    html = renderer.render("components/photo-grid.j2.html", context)
    soup = BeautifulSoup(html, 'html.parser')
    
    grid_container = soup.find('div')
    assert grid_container is not None
    
    # Check that custom classes are applied
    container_classes = ' '.join(grid_container.get('class', []))
    assert 'grid-cols-3' in container_classes
    assert 'gap-2' in container_classes
    assert 'p-2' in container_classes