from decouple import config

database_path_list = {
    'meloncloud': config('MELONCLOUD_DATABASE', default='')
}