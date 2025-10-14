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


def test_template_renderer_saves_rendered_html_to_file():
    """Test that renderer can save rendered HTML to output directory"""
    renderer = TemplateRenderer()
    
    # Mock file operations
    mock_open = Mock()
    mock_file = Mock()
    mock_open.return_value.__enter__ = Mock(return_value=mock_file)
    mock_open.return_value.__exit__ = Mock(return_value=None)
    
    with patch('builtins.open', mock_open):
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            renderer.save_html("<html>Test</html>", "prod/site/gallery.html")
            
            # Verify directory was created
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
            
            # Verify file was opened for writing
            mock_open.assert_called_once_with("prod/site/gallery.html", "w")
            
            # Verify HTML was written
            mock_file.write.assert_called_once_with("<html>Test</html>")