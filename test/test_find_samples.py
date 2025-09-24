import pytest
import click

from src.command import find_samples


class TestFindSamplesCommand:
    def test_command_exists(self):
        assert hasattr(find_samples, 'find_samples')
    
    def test_find_samples_is_click_command(self):
        assert isinstance(find_samples.find_samples, click.core.Command)