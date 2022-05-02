from pathlib import Path

from fastapi.templating import Jinja2Templates
from src.tools.log import log as Log

BASE_DIR = str(Path(__file__).resolve().parent)
SRC_DIR = BASE_DIR[:BASE_DIR.find('/environments')]

templates = Jinja2Templates(directory=str(Path(SRC_DIR, 'static/templates')))
