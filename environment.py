from decouple import config

SECRET_KEY = config('SECRET_KEY', default=None)
TWITTER_SECRET_PASSWORD = config('TWITTER_SECRET_PASSWORD', default=None)
CONSUMER_KEY = config('CONSUMER_KEY', default=None)
CONSUMER_SECRET = config('CONSUMER_SECRET', default=None)
ACCESS_TOKEN = config('ACCESS_TOKEN', default=None)
ACCESS_TOKEN_SECRET = config('ACCESS_TOKEN_SECRET', default=None)

CONSUMER_KEY_V2 = config('CONSUMER_KEY_V2', default=None)
CONSUMER_SECRET_V2 = config('CONSUMER_SECRET_V2', default=None)
ACCESS_TOKEN_V2 = config('ACCESS_TOKEN_V2', default=None)
ACCESS_TOKEN_SECRET_V2 = config('ACCESS_TOKEN_SECRET_V2', default=None)
BEARER_TOKEN_V2 = config('BEARER_TOKEN_V2', default=None)
GITHUB_ACCESS_TOKEN = config('GITHUB_ACCESS_TOKEN', default=None)
OPENSSL_SECRET_KEY = config('OPENSSL_SECRET_KEY', default=None)
