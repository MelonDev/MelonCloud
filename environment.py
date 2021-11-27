from decouple import config

SECRET_KEY = config('SECRET_KEY', default=None)
TWITTER_SECRET_PASSWORD = config('TWITTER_SECRET_PASSWORD', default=None)
CONSUMER_KEY = config('CONSUMER_KEY', default=None)
CONSUMER_SECRET = config('CONSUMER_SECRET', default=None)
ACCESS_TOKEN = config('ACCESS_TOKEN', default=None)
ACCESS_TOKEN_SECRET = config('ACCESS_TOKEN_SECRET', default=None)
