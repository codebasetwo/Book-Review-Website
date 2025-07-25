from typing import List, Any
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from fastapi import Request, status, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.exceptions import HTTPException
from abc import abstractmethod
from .utils import decode_token
from src.db.redis import token_in_blocklist
from .service import UserService
from src.db.main import get_session
from src.db.models import User
from src.errors import (InvalidToken,
                        InsufficientPermission,
                        InvalidCredentials,
                        RefreshTokenRequired,
                        AccessTokenRequired, 
                        AccountNotVerified)


user_service = UserService()

class TokenBearer(HTTPBearer):
    def __init__(self, auto_error = True):
        super().__init__(auto_error=auto_error)


    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials| None:
        creds = await super().__call__(request)
        token = creds.credentials
        token_data = decode_token(token)
        if not self.is_token_valid(token):
            raise InvalidToken()
            # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={
            #         "error":"This token is invalid or expired",
            #         "resolution":"Please get new token"
            #     })
        
        self.verify_token_data(token_data)
        
        if token_data["refresh"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail={"error": "This token is invalid or expired",
                                        "resolution": "Please get a new token"
                                        },)
        
       
        if await token_in_blocklist(token_data["jti"]):
            raise InvalidToken()
        
        return token_data

    def is_token_valid(self, token) -> bool:
        token_data = decode_token(token)
        return True if token_data else False
    
    #@abstractmethod
    def verify_token_data(self, token_data):
        raise NotImplementedError("Please Override this method in child classes")

    
    

class AccessTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict) -> None:
        if token_data and token_data["refresh"]:
            raise AccessTokenRequired()


class RefreshTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict) -> None:
        if token_data and not token_data["refresh"]:
            raise RefreshTokenRequired()
#                                 {
#   "email": "nnaemeka@ubuntu.com",
#   "password": "fortytwo"
# }

async def get_current_user(
    token_details: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    user_email = token_details["user"]["email"]

    user = await user_service.get_user_by_email(user_email, session)

    return user


class RoleChecker:
    def __init__(self, allowed_roles: List[str]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> Any:
        if not current_user.is_verified:
            raise AccountNotVerified()
        if current_user.role in self.allowed_roles:
            return True

        raise InsufficientPermission()
    # InsufficientPermission()