import secrets
import base64


def generate_totp_secret(length=20):
    random_bytes = secrets.token_bytes(length)
    secret = base64.b32encode(random_bytes).decode('utf-8').rstrip('=')
    return secret


print(generate_totp_secret(20))
