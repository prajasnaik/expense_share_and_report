from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from base64 import b64encode, b64decode




class UserAuth():
    def __init__(self) -> None:
        self.public_key = self.load_public_key()
        self.private_key = self.load_private_key()

    def load_public_key(self) -> None:
        with open("keys/public_key.pem", "rb") as key_file:
            public_key = serialization.load_pem_public_key(key_file.read())
        return public_key

    def load_private_key(self) -> None:
        with open("keys/private_key.pem", "rb") as key_file:
            private_key = serialization.load_pem_private_key(key_file.read(), password=None)
        return private_key

    def encode(self, message: str) -> str:
        encrypted = self.public_key.encrypt(
            message.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return b64encode(encrypted).decode()

    def decode(self, encrypted_message: str) -> str:
        decrypted = self.private_key.decrypt(
            b64decode(encrypted_message),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted.decode()

   
