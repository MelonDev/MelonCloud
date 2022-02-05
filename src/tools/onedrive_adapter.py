import datetime as dt
import httpx
from fastapi import requests

from environment import IFTTT_SECRET_KEY

client = httpx.AsyncClient()


async def send_url_to_onedrive(medias):
    # icloud_url = f'https://maker.ifttt.com/trigger/save_image_to_icloud_photo/with/key/{IFTTT_SECRET_KEY}'
    onedrive_url = f'https://maker.ifttt.com/trigger/save_file_to_onedrive/with/key/{IFTTT_SECRET_KEY}'

    now = dt.datetime.now()
    year = str(now.year)

    for media in medias:
        name = media["name"]
        type = media["type"]
        url = media["url"]
        url_media = str(url) + "?format=jpg&name=orig" if type == "photo" else str(url)

        name_media = str(name) + ".jpg" if type == "photo" else str(name) + ".mp4"
        type_media = "Photos" if type == "photo" else "Videos"

        type_media_with_year = str(type_media) + "/" + year

        onedrive_data = {'value1': name_media, 'value2': type_media_with_year, 'value3': url_media}
        await client.post(onedrive_url, json=onedrive_data)
