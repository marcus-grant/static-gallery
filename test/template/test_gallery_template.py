from bs4 import BeautifulSoup
from src.services.template_renderer import TemplateRenderer


def test_gallery_template_has_basic_structure():
  """Test that gallery template contains expected HTML structure"""
  renderer = TemplateRenderer()
  photo_data = {"photos": []}
  
  html = renderer.render_gallery(photo_data)
  soup = BeautifulSoup(html, 'html.parser')
  
  # Check for required meta tags
  assert soup.find('meta', {'name': 'robots', 'content': 'noindex, nofollow'})
  assert soup.find('meta', {'name': 'viewport'})
  
  # Check for Alpine.js data attribute
  assert soup.find(attrs={'x-data': True})
  
  # Check for photo grid container
  assert soup.find(class_='grid')