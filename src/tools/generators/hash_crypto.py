from passlib.context import CryptContext

pwd_cxt = CryptContext(schemes=["bcrypt"])


class HashCrypt:

    def bcrypt(self, value: str):
        return pwd_cxt.hash(value)

    def verify(self, hash: str, plain: str):
        return pwd_cxt.verify(plain, hash)
