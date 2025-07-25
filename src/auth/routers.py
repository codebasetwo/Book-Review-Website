from datetime import timedelta, datetime


from fastapi import APIRouter, Depends, status, BackgroundTasks
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse


from sqlmodel.ext.asyncio.session import AsyncSession
from .dependencies import RefreshTokenBearer, AccessTokenBearer,  get_current_user
from .schemas import UserCreateModel, UserModel, UserLoginModel, UserBooksModel, EmailModel, PasswordResetRequestModel, PasswordResetConfirmModel
from .service import UserService
from src.db.main import get_session
from .utils import create_access_token, verify_passwd, create_url_safe_token, decode_url_safe_token, generate_passwd_hash
from src.db.redis import add_jti_to_blocklist
from .dependencies import RoleChecker
from src.mail import create_message
from src.celery_tasks import send_email
from src.mail import mail
from src.config import Config
from src.errors import UserNotFound


user_service = UserService()
auth_router = APIRouter()
role_checker = RoleChecker(["admin", "user"])
REFRESH_TOKEN_EXPIRY = 2

@auth_router.post("/send_mail")
async def send_mail(emails: EmailModel):
    emails = emails.addresses

    html = "<h1>Welcome to the app</h1>"
    subject = "Welcome to our app"
    # messages = create_message(
    #     recipients=[emails],
    #     subject="Welcome",
    #     body=html,
    # )
    # await mail.send_message(messages)
    send_email.delay(emails, subject, html)

    return {"message": "Email sent successfully"}


@auth_router.post("/signup",
                  status_code = status.HTTP_201_CREATED)
async def create_user_account(user_request: UserCreateModel,
                              bg_tasks: BackgroundTasks, 
                              session: AsyncSession= Depends(get_session)):
    email = user_request.email
    user_exists = await user_service.user_exist(email, session)

    if user_exists:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user already exists")
    token = create_url_safe_token({"email":email})
    new_user = await user_service.create_user(user_request, session)
    link = f"http://{Config.DOMAIN}/api/v1/auth/verify/{token}"
    html = f"""
    <h1>Verify your Email</h1>
    <p>Please click this <a href="{link}">link</a> to verify your email</p>
    """
    # messages = create_message(
    #     recipients=[email],
    #     subject="Verify your email",
    #     body=html,
    # )
    subject = "Verify your email"
    # bg_tasks.add_task(mail.send_message, messages)
    #await mail.send_message(messages)
    send_email.delay([email], subject, html)
    return {
        "messages": "Account created! Check email to verify",
        "user": new_user
        }


@auth_router.get("/verify/{token}")
async def verify_user_account(token: str, session: AsyncSession = Depends(get_session)):

    token_data = decode_url_safe_token(token)

    user_email = token_data.get("email")

    if user_email:
        user = await user_service.get_user_by_email(user_email, session)

        if not user:
            raise UserNotFound()

        await user_service.update_user(user, {"is_verified": True}, session)

        return JSONResponse(
            content={"message": "Account verified successfully"},
            status_code=status.HTTP_200_OK,
        )

    return JSONResponse(
        content={"message": "Error occured during verification"},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@auth_router.post("/login")
async def login_users(user_login: UserLoginModel, session: AsyncSession= Depends(get_session)):
    email = user_login.email
    passwd = user_login.password

    user = await user_service.get_user_by_email(email, session)
    if user:
        is_valid_passwd = verify_passwd(passwd, user.password_hash)

        if is_valid_passwd:
            access_token = create_access_token(
                user_data={
                    "email": user.email,
                    "user_uid": str(user.uid),
                    "role": user.role

                }
            )

            refresh_token = create_access_token(
                user_data={
                    "email": user.email,
                    "user_uid": str(user.uid)
                },
                refresh=True,
                expiry = timedelta(days=REFRESH_TOKEN_EXPIRY))


            return JSONResponse(
                content={
                    "message": "Login Successful",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": {
                        "email": user.email,
                        "uid": str(user.uid)
                    }
                }
            )
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail = "Invalid email or password")



@auth_router.get("/refresh_token")
async def get_new_access_token(token_details: dict = Depends(RefreshTokenBearer())):
    expiry_timestamp = token_details["exp"]

    if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
         new_access_token = create_access_token(user_data=token_details["user"])

         return JSONResponse(
             content={"access_token": new_access_token}
             )
    
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")



@auth_router.get("/me", response_model=UserBooksModel)
async def get_current_user(
    user=Depends(get_current_user), _: bool = Depends(role_checker)
):
    return user

@auth_router.get("/logout")
async def revoke_token(token_details: dict = Depends(AccessTokenBearer())):
    await add_jti_to_blocklist(token_details["jti"])

    return JSONResponse(
        content={"message": "Logged Out Successfully"}, status_code=status.HTTP_200_OK
    )



@auth_router.post("/password-reset-request")
async def password_reset_request(email_data: PasswordResetRequestModel):
    email = email_data.email

    token = create_url_safe_token({"email": email})

    link = f"http://{Config.DOMAIN}/api/v1/auth/password-reset-confirm/{token}"

    html_message = f"""
    <h1>Reset Your Password</h1>
    <p>Please click this <a href="{link}">link</a> to Reset Your Password</p>
    """
    subject = "Reset Your Password"

    send_email.delay([email], subject, html_message)
    return JSONResponse(
        content={
            "message": "Please check your email for instructions to reset your password",
        },
        status_code=status.HTTP_200_OK,
    )


@auth_router.post("/password-reset-confirm/{token}")
async def reset_account_password(
    token: str,
    passwords: PasswordResetConfirmModel,
    session: AsyncSession = Depends(get_session),
):
    new_password = passwords.new_password
    confirm_password = passwords.confirm_new_password

    if new_password != confirm_password:
        raise HTTPException(
            detail="Passwords do not match", status_code=status.HTTP_400_BAD_REQUEST
        )

    token_data = decode_url_safe_token(token)

    user_email = token_data.get("email")

    if user_email:
        user = await user_service.get_user_by_email(user_email, session)

        if not user:
            raise UserNotFound()

        passwd_hash = generate_passwd_hash(new_password)
        await user_service.update_user(user, {"password_hash": passwd_hash}, session)

        return JSONResponse(
            content={"message": "Password reset Successfully"},
            status_code=status.HTTP_200_OK,
        )

    return JSONResponse(
        content={"message": "Error occured during password reset."},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )