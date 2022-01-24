from decouple import config

SECRET_KEY = config('SECRET_KEY', default=None)

TWITTER_SECRET_PASSWORD = config('TWITTER_SECRET_PASSWORD', default=None)
TWITTER_REFRESH_SECRET_PASSWORD = config('TWITTER_REFRESH_SECRET_PASSWORD', default=None)

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

FIREBASE_PROJECT_ID = config('FIREBASE_PROJECT_ID', default="")
FIREBASE_PRIVATE_KEY_ID = config('FIREBASE_PRIVATE_KEY_ID', default="")
FIREBASE_PRIVATE_KEY = config('FIREBASE_PRIVATE_KEY', default="")
FIREBASE_CLIENT_EMAIL = config('FIREBASE_CLIENT_EMAIL', default="")
FIREBASE_CLIENT_ID = config('FIREBASE_CLIENT_ID', default="")
FIREBASE_CLIENT_X509_CERT_URL = config('FIREBASE_CLIENT_X509_CERT_URL', default="")


