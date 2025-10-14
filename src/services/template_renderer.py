from jinja2 import Environment, FileSystemLoader
from pathlib import Path


class TemplateRenderer:
    def __init__(self):
        template_dir = Path("templates")
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
    
    def render_gallery(self, photo_data):
        template = self.env.get_template("gallery.j2.html")
        return template.render(photo_data)
    
    def save_html(self, html_content, output_path):
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(html_content)