from unittest.mock import Mock, patch
from src.services.template_renderer import TemplateRenderer


def test_template_renderer_initializes_jinja2_environment():
    """Test that renderer initializes Jinja2 environment with template directory"""
    renderer = TemplateRenderer()
    
    assert renderer.env is not None
    assert renderer.env.loader is not None


def test_template_renderer_calls_correct_template_for_gallery():
    """Test that render_gallery calls the correct template with provided data"""
    renderer = TemplateRenderer()
    
    # Mock the template
    mock_template = Mock()
    mock_template.render.return_value = "<html>Gallery HTML</html>"
    
    # Mock the environment to return our mock template
    with patch.object(renderer.env, 'get_template', return_value=mock_template) as mock_get:
        photo_data = {"photos": [{"filename": "test.jpg"}]}
        html = renderer.render_gallery(photo_data)
        
        # Verify correct template was requested
        mock_get.assert_called_once_with("gallery.j2.html")
        
        # Verify template was rendered with exact data provided
        mock_template.render.assert_called_once_with(photo_data)
        
        # Verify we got the rendered result
        assert html == "<html>Gallery HTML</html>"