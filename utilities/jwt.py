import jwt
import requests

from datetime import datetime, timedelta
from jwt import PyJWTError
from typing import Dict, Union

from abstractions.utility import IUtility

from start_utils import logger, SECRET_KEY, HS256_ALGORITHM, RS256_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, GOOGLE_JWKS_URL, GOOGLE_CLIENT_ID


class JWTUtility(IUtility):

    def __init__(self, urn: str = None) -> None:
        super().__init__(urn)
        self.urn = urn
        self.logger = logger
        self.jwks = self.get_google_jwks()

    def create_access_token(self, data: dict) -> str:

        to_encode = data.copy()
        if ACCESS_TOKEN_EXPIRE_MINUTES:
            expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        else:
            expire = datetime.now() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=HS256_ALGORITHM)

        return encoded_jwt

    def get_google_jwks(self):

        self.logger.debug("Generating JWKS")
        response = requests.get(GOOGLE_JWKS_URL)
        self.logger.debug("Generated JWKS")

        return response.json()

    def get_rsa_public_key(self, kid: str):
        
        self.logger.debug("Generating public key")
        for key in self.jwks['keys']:

            if key['kid'] == kid:
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)

                self.logger.debug("Generated public key")
                return public_key

        self.logger.debug("Failed to generate public key")
        return None

    def decode_token(self, token: str) -> Union[Dict[str, str]]:

        try:
            
            self.logger.debug("Fetching jwt headers")
            unverified_header = jwt.get_unverified_header(token)
            alg = unverified_header.get('alg')
            kid = unverified_header.get('kid')
            self.logger.debug("Fetched jwt headers")

            if alg == HS256_ALGORITHM:

                self.logger.debug(f"Algorithm used is {HS256_ALGORITHM}")

                self.logger.debug("Decoding jwt token")
                payload = jwt.decode(token, SECRET_KEY, algorithms=[HS256_ALGORITHM])
                self.logger.debug("Decoded jwt token")

            elif alg == RS256_ALGORITHM and kid:

                self.logger.debug(f"Algorithm used is {RS256_ALGORITHM}")

                public_key = self.get_rsa_public_key(kid)
                if not public_key:

                    self.logger.error(f"Unable to find public key for kid: {kid}")
                    raise PyJWTError(f"Unable to find public key for kid: {kid}")

                self.logger.debug("Decoding jwt token")
                payload = jwt.decode(token, public_key, algorithms=[RS256_ALGORITHM], audience=GOOGLE_CLIENT_ID)
                self.logger.debug("Decoded jwt token")

            else:

                self.logger.error(f"Unsupported token algorithm: {RS256_ALGORITHM}")
                raise PyJWTError(f"Unsupported token algorithm: {RS256_ALGORITHM}")

            return payload

        except PyJWTError as err:
            self.logger.error(f"Token decoding error: {err}")
            raise err