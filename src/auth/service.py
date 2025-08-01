
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from src.db.models import User
from .schemas import UserCreateModel
from .utils import generate_passwd_hash

class UserService:

    async def get_user_by_email(self, email: str, session: AsyncSession):
        statement = select(User).where(User.email == email)

        result = await session.exec(statement)

        user = result.first()

        return user
    

    async def user_exist(self, email: str, session: AsyncSession) -> bool:

        user = await self.get_user_by_email(email, session)

        return True if user else False
    

    async def create_user(self, request: UserCreateModel, session: AsyncSession):
        user_dict = request.model_dump()

        new_user = User(
            **user_dict
        )

        new_user.password_hash = generate_passwd_hash(user_dict["password"])
        new_user.role = "user"
        session.add(new_user)
        await session.commit()

        return new_user
    
    async def update_user(self, user:User , user_data: dict, session:AsyncSession):

        for k, v in user_data.items():
            setattr(user, k, v)

        await session.commit()

        return user