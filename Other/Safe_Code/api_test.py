import requests


def generate_password(api_url, length, lowercase, uppercase, digits, punctuation):
    payload = {
        "length": length,
        "lowercase": lowercase,
        "uppercase": uppercase,
        "digits": digits,
        "punctuation": punctuation
    }
    response = requests.post(api_url, json=payload)

    if response.status_code == 200:
        return response.json().get("password")
    else:
        return f"Error: {response.status_code}, {response.text}"


if __name__ == "__main__":
    api_url = "http://localhost:25698/generate-password/"
    length = 12
    lowercase = True
    uppercase = True
    digits = True
    punctuation = True

    password = generate_password(api_url, length, lowercase, uppercase, digits, punctuation)
    print(f"Generated Password: {password}")
