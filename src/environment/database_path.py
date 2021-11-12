from decouple import config

database_path_list = {
    'meloncloud': config('MELONCLOUD_DATABASE', default=None)
}

database_path = {k: v for k, v in database_path_list.items() if v is not None}


