import datetime
import jwt
import requests

from config import TESSERACT_API_SECRET

def request_to_tesseract(endpoint):
    '''
    Make a request to tesseract with authentication.
    '''
    JWT_ALGORITHM = 'HS256'
    JWT_EXP_DELTA_MINUTES = 30

    payload = {
      'auth_level': 10,
      'sub': 'c58b2eed-0aac-92f4-e4ce-2c707bafec8f',
      'status': 'valid',
      'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=JWT_EXP_DELTA_MINUTES)
    }

    jwt_token = jwt.encode(payload, TESSERACT_API_SECRET, JWT_ALGORITHM)

    headers = {
      "x-tesseract-jwt-token": jwt_token
    }

    return requests.get(endpoint, headers=headers)