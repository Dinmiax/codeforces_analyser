from passlib.context import CryptContext

pwd_cxt = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Hash():
    def get_hash(password):
        print(password)
        return pwd_cxt.hash(password)

    def verify(hashed, plain):
        try:
            return pwd_cxt.verify(plain, hashed)
        except:
            return False
