import hashlib
import base58
import time
import json
from collections import namedtuple
import configparser
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import os

# Wallet
class Wallet:
    def __init__(self):
        self.public_key, self.private_key = self.create_wallet()
        self.balances = {}
        self.load_wallet()

    def create_wallet(self):
        # Use SHA256 to create public/private keys of 256-bit length
        # Store keys in Base58 encoding
        # Generate an RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Serialize the public key to store in Base58 encoding
        public_key_bytes = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # Calculate SHA256 hash of the public key
        sha256 = hashlib.sha256()
        sha256.update(public_key_bytes)
        hashed_public_key = sha256.digest()

        # Encode hashed public key in Base58
        encoded_public_key = base58.b58encode(hashed_public_key)

        # Serialize the private key to store in Base58 encoding
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        private_key = private_key_bytes.decode('utf-8')
        
        
         # Save keys to wallet.cfg
        config = configparser.ConfigParser()
        config['Keys'] = {
            'public_key': encoded_public_key.decode('utf-8'),
            'private_key': private_key
        }

        with open('wallet.cfg', 'w') as configfile:
            config.write(configfile)

        return encoded_public_key, private_key
    
    def load_keys_from_config(self):
        config = configparser.ConfigParser()
        config.read('wallet.cfg')
        public_key = config['Keys']['public_key']
        private_key = config['Keys']['private_key']
        return public_key, private_key

    def get_balance(self):
        public_key, _ = self.load_keys_from_config()

        # Check if the public key is in the balances dictionary
        if public_key in self.balances:
            return self.balances[public_key]
        else:
            return 0.0  # If not found, balance is 0


    def send_coins(self, recipient, value):
        sender_public_key, _ = self.load_keys_from_config()

        # Check if sender has enough balance
        if self.balances.get(sender_public_key, 0.0) >= value:
            # Update sender's balance (subtract the value)
            self.balances[sender_public_key] -= value

            # Update recipient's balance (add the value)
            if recipient in self.balances:
                self.balances[recipient] += value
            else:
                self.balances[recipient] = value

            print(f"Transaction successful. Sent {value} coins to {recipient}")
        else:
            print("Insufficient balance to perform the transaction")
            
    '''def load_wallet(self):
        # Load existing wallet from wallet.cfg if it exists
        if os.path.exists('wallet.cfg'):
            config = configparser.ConfigParser()
            config.read('wallet.cfg')
            if 'Keys' in config:
                self.public_key = (config['Keys']['public_key'])
                self.private_key = (config['Keys']['private_key']) '''

    def print_public_key(self):
        if hasattr(self, 'public_key'):
            print(f"Public Key: {self.public_key}")
        else:
            print("Wallet not loaded. Create or load a wallet first.")

    def print_private_key(self):
        if hasattr(self, 'private_key'):
            print(f"Private Key: {self.private_key}")
        else:
            print("Wallet not loaded. Create or load a wallet first.")
