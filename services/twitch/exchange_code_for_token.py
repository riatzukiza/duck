import requests
import os

CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
CLIENT_SECRET= os.getenv('TWITCH_SECRET')
AUTH_CODE=os.getenv('TWITCH_AUTH_CODE')

REDIRECT_URI = 'http://localhost'


token_url = 'https://id.twitch.tv/oauth2/token'

token_params = {
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'code': AUTH_CODE,
    'grant_type': 'authorization_code',
    'redirect_uri': REDIRECT_URI,
}

response = requests.post(token_url, params=token_params)
token_data = response.json()
print("Access Token Response:", token_data)