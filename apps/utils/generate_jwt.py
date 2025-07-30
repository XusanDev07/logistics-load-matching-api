from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

ENCODE_USER_FIELDS = ('full_name')


def generate_jwt_token(user: get_user_model()):
    token = RefreshToken.for_user(user)
    token.payload.update({key: getattr(user, key, '') for key in ENCODE_USER_FIELDS})
    return token
