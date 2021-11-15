from pathlib import Path

from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
print("BB"+str(BASE_DIR))

templates = Jinja2Templates("")

def get_template(BASE_DIR):
    return Jinja2Templates(directory=str(Path(BASE_DIR, 'static/templates')))
