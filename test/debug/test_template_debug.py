from unittest.mock import patch, Mock
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from debug.template_debug import TemplateDebugger, debug_gallery, debug_photo_cell, analyze_html


def test_template_debugger_initializes():
    """Test that TemplateDebugger initializes with renderer"""
    debugger = TemplateDebugger()
    assert debugger.renderer is not None


def test_debug_gallery_generates_sample_photos():
    """Test that debug_gallery creates sample photo data"""
    debugger = TemplateDebugger()
    
    with patch.object(debugger, 'render_and_print') as mock_render:
        mock_render.return_value = "<html>test</html>"
        
        debugger.debug_gallery(photo_count=3)
        
        # Verify render_and_print was called
        mock_render.assert_called_once()
        
        # Check the data passed to render_and_print
        args = mock_render.call_args[0]
        data = args[1]  # Second argument is the data
        
        assert "photos" in data
        assert len(data["photos"]) == 3
        
        # Check sample photo structure
        photo = data["photos"][0]
        assert "filename" in photo
        assert "thumb_url" in photo
        assert "web_url" in photo
        assert "wedding-sample-1" in photo["filename"]


def test_debug_photo_cell_creates_proper_data():
    """Test that debug_photo_cell creates proper photo data structure"""
    debugger = TemplateDebugger()
    
    with patch.object(debugger, 'render_and_print') as mock_render:
        mock_render.return_value = "<div>test</div>"
        
        debugger.debug_photo_cell()
        
        # Verify render_and_print was called
        mock_render.assert_called_once()
        
        # Check the data structure
        args = mock_render.call_args[0]
        data = args[1]
        
        assert "photo" in data
        assert "filename" in data["photo"]
        assert "thumb_url" in data["photo"]
        assert "web_url" in data["photo"]


def test_analyze_template_structure():
    """Test that template analysis provides correct metrics"""
    sample_html = """
    <html>
        <body>
            <div x-data="test()" class="grid md:grid-cols-4">
                <img src="/test.jpg" alt="test">
                <div @click="test()">Click me</div>
                <div class="lg:grid-cols-6">More content</div>
            </div>
        </body>
    </html>
    """
    
    debugger = TemplateDebugger()
    
    with patch('builtins.print'):  # Suppress print output
        analysis = debugger.analyze_template_structure(sample_html)
    
    assert analysis["images"] == 1
    assert analysis["clickable_elements"] == 1
    assert analysis["alpine_data_elements"] == 1
    assert analysis["grid_containers"] >= 1
    assert "md:grid-cols-4" in analysis["responsive_classes"]
    assert "lg:grid-cols-6" in analysis["responsive_classes"]


def test_convenience_functions_work():
    """Test that convenience functions call the debugger correctly"""
    
    with patch('debug.template_debug.TemplateDebugger') as mock_debugger_class:
        mock_debugger = Mock()
        mock_debugger_class.return_value = mock_debugger
        
        # Test debug_gallery convenience function
        debug_gallery(5)
        mock_debugger.debug_gallery.assert_called_once_with(5)
        
        # Test debug_photo_cell convenience function  
        debug_photo_cell()
        mock_debugger.debug_photo_cell.assert_called_once()


def test_analyze_html_convenience_function():
    """Test analyze_html convenience function"""
    test_html = "<div>test</div>"
    
    with patch('debug.template_debug.TemplateDebugger') as mock_debugger_class:
        mock_debugger = Mock()
        mock_debugger_class.return_value = mock_debugger
        
        analyze_html(test_html)
        mock_debugger.analyze_template_structure.assert_called_once_with(test_html)


def test_render_and_print_formats_output():
    """Test that render_and_print calls template method and formats output"""
    debugger = TemplateDebugger()
    
    mock_template_method = Mock(return_value="<div>test output</div>")
    test_data = {"test": "data"}
    
    with patch('builtins.print'):  # Suppress print output
        result = debugger.render_and_print(mock_template_method, test_data, "Test Title")
    
    # Verify template method was called with data
    mock_template_method.assert_called_once_with(test_data)
    
    # Verify return value
    assert result == "<div>test output</div>"