# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

# Requires: pycryptodome
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import json


class CDOCrypto:
    @staticmethod
    def encrypt_creds(username, password, lar):
        # lar['larPublicKey']['encodedKey']
        key = RSA.importKey(base64.b64decode(lar["larPublicKey"]["encodedKey"]))
        encryptor = PKCS1_v1_5.new(key)
        enc_creds = json.dumps(
            {
                "keyId": lar["larPublicKey"]["keyId"],
                "username": base64.b64encode(encryptor.encrypt(username.encode(encoding="UTF-8"))).decode(),
                "password": base64.b64encode(encryptor.encrypt(password.encode(encoding="UTF-8"))).decode(),
            }
        )

        return {"credentials": enc_creds}
