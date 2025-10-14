from unittest.mock import Mock, patch, call
from src.services.static_assets import StaticAssetService


def test_static_asset_service_copies_css_files():
    """Test that service can copy CSS files to output directory"""
    service = StaticAssetService()
    
    # Mock file operations
    with patch('src.services.static_assets.Path') as mock_path_class:
        with patch('src.services.static_assets.shutil.copy2') as mock_copy:
            # Set up mock paths
            mock_source = Mock()
            mock_output = Mock()
            mock_path_class.side_effect = lambda x: mock_source if x == "static/css" else mock_output
            
            # Mock source directory exists and has CSS files
            mock_source.exists.return_value = True
            mock_css_file = Mock()
            mock_css_file.name = 'styles.css'
            mock_source.glob.return_value = [mock_css_file]
            
            # Mock output path operations
            mock_output.__truediv__ = Mock(return_value=Mock())
            
            result = service.copy_css_files("static/css", "prod/site/css")
            
            # Verify directory was created
            mock_output.mkdir.assert_called_once_with(parents=True, exist_ok=True)
            
            # Verify file was copied
            mock_copy.assert_called_once()
            
            assert result['success'] is True
            assert result['copied'] == 1


def test_static_asset_service_generates_photos_json():
    """Test that service generates photos.json from photo data"""
    service = StaticAssetService()
    
    photo_data = {
        "photos": [
            {
                "filename": "wedding-20250809T132034.000Z+0200-r5a-001.jpg",
                "timestamp": "20250809T132034.000Z+0200",
                "camera": "r5a",
                "sequence": "001"
            }
        ]
    }
    
    # Mock file operations
    mock_open = Mock()
    mock_file = Mock()
    mock_open.return_value.__enter__ = Mock(return_value=mock_file)
    mock_open.return_value.__exit__ = Mock(return_value=None)
    
    with patch('builtins.open', mock_open):
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            result = service.generate_photos_json(photo_data, "prod/site/photos.json")
            
            # Verify directory was created
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
            
            # Verify file was opened for writing
            mock_open.assert_called_once_with("prod/site/photos.json", "w")
            
            # Verify JSON was written (json.dump calls write multiple times)
            assert mock_file.write.called
            
            # Check the combined content of all write calls
            all_written = ''.join(call[0][0] for call in mock_file.write.call_args_list)
            assert '"photos"' in all_written
            assert 'wedding-20250809T132034.000Z+0200-r5a-001.jpg' in all_written
            
            assert result['success'] is True