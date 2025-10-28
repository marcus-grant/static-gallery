from bs4 import BeautifulSoup
from src.services.template_renderer import TemplateRenderer


def test_base_template_includes_tailwind_cdn():
    """Test that base template includes Tailwind CSS from CDN"""
    renderer = TemplateRenderer()
    photo_data = {"photos": []}
    
    html = renderer.render("gallery.j2.html", photo_data)
    soup = BeautifulSoup(html, 'html.parser')
    
    # Check for Tailwind CSS CDN link
    tailwind_link = soup.find('script', src=lambda x: x and 'tailwindcss' in x)
    assert tailwind_link is not None
    assert 'cdn.tailwindcss.com' in tailwind_link['src']


# TODO: Not ready for Alpine.js tests - post-deployment feature
# def test_base_template_includes_alpinejs_cdn():
#     """Test that base template includes Alpine.js from CDN"""
#     renderer = TemplateRenderer()
#     photo_data = {"photos": []}
#     
#     html = renderer.render("gallery.j2.html", photo_data)
#     soup = BeautifulSoup(html, 'html.parser')
#     
#     # Check for Alpine.js CDN script
#     alpine_script = soup.find('script', src=lambda x: x and 'alpinejs' in x)
#     assert alpine_script is not None
#     assert 'defer' in alpine_script.attrs
#     assert 'cdn.jsdelivr.net' in alpine_script['src']


# TODO: Not ready for Alpine.js tests - post-deployment feature
# def test_alpine_js_initialization_element_exists():
#     """Test that template has element with Alpine.js x-data attribute"""
#     renderer = TemplateRenderer()
#     photo_data = {"photos": []}
#     
#     html = renderer.render("gallery.j2.html", photo_data)
#     soup = BeautifulSoup(html, 'html.parser')
#     
#     # Check for x-data attribute (Alpine.js initialization)
#     alpine_element = soup.find(attrs={'x-data': True})
#     assert alpine_element is not None
#     assert 'photoGallery()' in alpine_element['x-data']


def test_base_template_has_proper_html_structure():
    """Test that template has proper HTML5 structure"""
    renderer = TemplateRenderer()
    photo_data = {"photos": []}
    
    html = renderer.render("gallery.j2.html", photo_data)
    soup = BeautifulSoup(html, 'html.parser')
    
    # Check for proper HTML5 structure
    assert soup.find('html', {'lang': 'en'})
    assert soup.find('head')
    assert soup.find('body')
    assert soup.find('meta', {'charset': 'UTF-8'})