import datetime
import jwt
import requests

def request_to_tesseract(endpoint, auth=None):
    '''
    Make a request to the tesseract api endpoint. 
    If you want to make a request with authentication required, please add as a second parameter to the function call the TESSERACT_API_SECRET variable.
    '''

    if auth != None:
      JWT_ALGORITHM = 'HS256'
      JWT_EXP_DELTA_MINUTES = 30

      payload = {
        'auth_level': 2,
        'sub': 'server',
        'status': 'valid',
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=JWT_EXP_DELTA_MINUTES)
      }

      jwt_token = jwt.encode(payload, auth, JWT_ALGORITHM)

      headers = {
        "x-tesseract-jwt-token": jwt_token
      }

      response = requests.get(endpoint, headers=headers)
    else:
      response = requests.get(endpoint)

    return response