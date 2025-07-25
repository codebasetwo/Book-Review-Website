
from datetime import timedelta, datetime
import logging
import uuid
import jwt
from passlib.context import CryptContext
from itsdangerous import URLSafeTimedSerializer

from src.config import Config

passwd_ctx = CryptContext(
    schemes=["bcrypt"]
)


ACCESS_TOKEN_EXPIRY = 3600

def generate_passwd_hash(passwd: str)-> str:
    hash = passwd_ctx.hash(passwd)

    return hash


def verify_passwd(passwd: str, hash: str) -> True:
    return passwd_ctx.verify(passwd, hash)


def create_access_token(user_data: dict, expiry: timedelta = None,
                        refresh: bool = False):
    payload = {
        "user": user_data,
        "exp": datetime.now() + (expiry if expiry else timedelta(seconds= ACCESS_TOKEN_EXPIRY)),
        "jti": str(uuid.uuid4()),
        "refresh": refresh,
    }
    token = jwt.encode(
        payload=payload,
        key= Config.JWT_SECRET,
        algorithm=Config.JWT_ALGORITHM,
    )

    return token

def decode_token(token: str) -> dict:
    try:
        token_data = jwt.decode(
            jwt=token, key=Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM]
        )

        return token_data

    except jwt.PyJWTError as jwte:
        logging.exception(jwte)
        return None
    except Exception as e:
        logging.exception(e)
        return None

serializer = URLSafeTimedSerializer(
    secret_key=Config.JWT_SECRET, salt="email-configuration"
)


def create_url_safe_token(data: dict):

    token = serializer.dumps(data)

    return token

def decode_url_safe_token(token:str):
    try:
        token_data = serializer.loads(token)

        return token_data
    
    except Exception as e:
        logging.error(str(e))