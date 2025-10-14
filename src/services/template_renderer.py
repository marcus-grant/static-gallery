from jinja2 import Environment, FileSystemLoader
from pathlib import Path


class TemplateRenderer:
    def __init__(self):
        template_dir = Path("templates")
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
    
    def render_gallery(self, photo_data):
        template = self.env.get_template("gallery.j2.html")
        return template.render(photo_data)