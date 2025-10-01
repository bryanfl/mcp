import requests
import os
from dotenv import load_dotenv

load_dotenv()

class TokenClient:
    def __init__(self):
        self.url = os.getenv('CRM_TOKEN_URL')
        self.client_id = os.getenv('CRM_CLIENT_ID')
        self.resource = os.getenv('CRM_RESOURCE')
        self.client_secret = os.getenv('CRM_CLIENT_SECRET')
        self.grant_type = os.getenv('CRM_GRANT_TYPE', 'client_credentials')

    def get_token(self):
        data = {
            'client_id': self.client_id,
            'resource': self.resource,
            'client_secret': self.client_secret,
            'grant_type': self.grant_type
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        response = requests.post(self.url, data=data, headers=headers)
        response.raise_for_status()
        return response.json()