from mangum import Mangum

from src.app import app as fastapi

handler = Mangum(app=fastapi)
