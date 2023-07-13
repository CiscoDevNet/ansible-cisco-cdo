#!/usr/bin/python3
# Requires: pycryptodome
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import json


class CDOCrypto:
    @staticmethod
    def encrypt_creds(username, password, lar):
        # lar['larPublicKey']['encodedKey']
        key = RSA.importKey(base64.b64decode(lar['larPublicKey']['encodedKey']))
        encryptor = PKCS1_v1_5.new(key)
        enc_creds = json.dumps({
            "keyId": lar['larPublicKey']['keyId'],
            "username": base64.b64encode(encryptor.encrypt(username.encode(encoding="UTF-8"))).decode(),
            "password": base64.b64encode(encryptor.encrypt(password.encode(encoding="UTF-8"))).decode()
        })

        return {"credentials": enc_creds}
