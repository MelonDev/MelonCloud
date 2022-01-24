from environment import FIREBASE_PROJECT_ID, FIREBASE_PRIVATE_KEY_ID, FIREBASE_PRIVATE_KEY, FIREBASE_CLIENT_EMAIL, \
    FIREBASE_CLIENT_ID, FIREBASE_CLIENT_X509_CERT_URL


def create_credentials_file() -> dict:
    return {"type": "service_account", "project_id": FIREBASE_PROJECT_ID, "private_key_id": FIREBASE_PRIVATE_KEY_ID,
            "private_key": replace_key(FIREBASE_PRIVATE_KEY), "client_email": FIREBASE_CLIENT_EMAIL,
            "client_id": FIREBASE_CLIENT_ID,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": FIREBASE_CLIENT_X509_CERT_URL}


def replace_key(value: str):
    return value.replace('\\n', '\n')


def firebase_storage_url() -> str:
    return FIREBASE_PROJECT_ID + ".appspot.com"
