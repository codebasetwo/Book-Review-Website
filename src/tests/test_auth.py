from src.auth.schemas import UserCreateModel

def test_user_signup(fake_session, fake_user_service, test_client):
    user_data = {
        "username": "Mekuzee",
        "email":"nwankwonnaemeka21@gmail.com",
        "first_name":"Nnaemeka",
        "last_name":"Nwankwo",
        "password": "pytest"
    }
    response = test_client.post(
        url=f"/api/v1/auth/signup",
        json= user_data
        
        )
    user = UserCreateModel(**user_data)

    assert fake_user_service.user_exists_called_once()
    assert fake_user_service.user_exists_called_once_with(user_data['email'],fake_session)
    assert fake_user_service.create_user_called_once()
    assert fake_user_service.create_user_called_once_with(user,fake_session)