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
import datetime
import sys
import random

app_info = "DSC: DataSys Coin Blockchain v1.0"


class Wallet:
    def __init__(self):
        self.public_key = None
        self.private_key = None
        self.balances = {}

    def get_current_date_time(self):
        return datetime.datetime.now().strftime("%Y%m%d %H:%M:%S.%f")

    def load_keys_from_config(self):
        config = configparser.ConfigParser()
        config.read('dsc_config.yaml')
        public_key = config['Keys']['public_key']
        private_key = config['Keys']['private_key']
        return public_key, private_key

    def load_wallet(self):
        if os.path.exists('dsc_config.yaml'):
            config = configparser.ConfigParser()
            config.read('dsc_config.yaml')
            if 'Keys' in config:
                self.public_key = config['Keys']['public_key']
                self.private_key = config['Keys']['private_key']

    def create_wallet(self):
        self.load_wallet()
        public_key = None
        private_key = None
        if not os.path.exists('dsc_config.yaml') and not os.path.exists('dsc-key.yaml'):
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
            public_key = base58.b58encode(hashed_public_key)

            # Serialize the private key to store in Base58 encoding
            private_key_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
            private_key = private_key_bytes.decode('utf-8')
            public_key = public_key.decode('utf-8')

            config = configparser.ConfigParser()
            config['Keys'] = {
                'public_key': public_key,
                'private_key': private_key
            }

            with open('dsc_config.yaml', 'w') as configfile:
                config.write(configfile)

            with open('dsc-key.yaml', 'w') as keyfile:
                keyfile.write(private_key)

            print(f"{self.get_current_date_time()} DSC v1.0\n{self.get_current_date_time()} DSC Public Address: {public_key}\n{self.get_current_date_time()} DSC Private Address: {private_key}\n{self.get_current_date_time()} Saved public key to dsc_config.yaml and private key to dsc-key.yaml in local folder")
        else:

            print(f"{self.get_current_date_time()} DSC v1.0\n{self.get_current_date_time()} Wallet already exists at dsc-key.yaml, wallet create aborted")

        return public_key, private_key

    def print_keys(self):
        self.load_wallet()
        if hasattr(self, 'public_key'):
            print(f"{self.get_current_date_time()} DSC v1.0\n{self.get_current_date_time()} Reading dsc_config.yaml and dsc-key.yaml...\n{self.get_current_date_time()} DSC Public Address: {self.public_key}\n{self.get_current_date_time()} DSC Private Address: {self.private_key}")

        else:
            print(f"{self.get_current_date_time()} DSC v1.0\n{self.get_current_date_time()} Error in finding key information, ensure that dsc_config.yaml and dsc-key.yaml exist and that they contain the correct information. You may need to run “./dsc wallet create”")

    def get_balance(self):
        if self.public_key in self.balances:
            print(
                f"{self.get_current_date_time()} DSC v1.0\n{self.get_current_date_time()} DSC Wallet balance: {self.balances[self.public_key]} coins at block x")
            return self.balances[self.public_key]
        else:
            print(f"{self.get_current_date_time()} DSC v1.0\n{self.get_current_date_time()} DSC Wallet balance:0.0 coins at block x")
            return 0.0

    def send_coins(self, value, recipient):
        self.load_wallet()
        sender_public_key = self.public_key
        print(self.balances, self.public_key,
              self.balances.get(sender_public_key))
        if self.balances.get(sender_public_key, 0.0) >= value:
            print("send_coins")
            self.balances[sender_public_key] -= value

            if recipient in self.balances:
                self.balances[recipient] += value
            else:
                self.balances[recipient] = value

            transaction_id = self.generate_transaction_id()

            print(f"{self.get_current_date_time()} DSC v1.0")
            print(
                f"{self.get_current_date_time()} DSC Wallet balance: {self.get_balance()} coins at block X")
            print(
                f"{self.get_current_date_time()} Created transaction {transaction_id}, Sending {value} coins to {recipient}")
            print(
                f"{self.get_current_date_time()} Transaction {transaction_id} submitted to pool")

            status = "submitted"
            for _ in range(5):  # Simulate status check for 5 seconds
                print(
                    f"{self.get_current_date_time()} Transaction {transaction_id} status [{status}]")
                time.sleep(1)  # Simulate waiting 1 second

                if status == "submitted":
                    status = "unconfirmed"
                elif status == "unconfirmed":
                    status = "confirmed"
                    break  # Transaction confirmed, break out of loop

            print(
                f"{self.get_current_date_time()} Transaction {transaction_id} status [confirmed], block X")
            print(
                f"{self.get_current_date_time()} DSC Wallet balance: {self.get_balance()} coins at block X")

    def generate_transaction_id(self):
        # Generate a random transaction ID
        return ''.join(random.choices('0123456789ABCDEF', k=16))

    def check_transaction_status(self, transaction_id):
        # Simulating contacting the pool server
        pool_response = self.contact_pool_server(transaction_id)

        if pool_response == "unknown":
            # Simulate contacting the blockchain server for transaction status
            blockchain_response = self.query_blockchain(transaction_id)

            if blockchain_response == "confirmed":
                print(f"{self.get_current_date_time()} DSC v1.0")
                print(
                    f"{self.get_current_date_time()} Transaction {transaction_id} status [confirmed]")
            else:
                print(f"{self.get_current_date_time()} DSC v1.0")
                print(
                    f"{self.get_current_date_time()} Transaction {transaction_id} status [unknown]")
        else:
            print(f"{self.get_current_date_time()} DSC v1.0")
            print(
                f"{self.get_current_date_time()} Transaction {transaction_id} status [{pool_response}]")

    def contact_pool_server(self, transaction_id):
        # Simulate contacting the pool server
        # Return a random status: submitted, unconfirmed, or unknown
        return random.choice(["submitted", "unconfirmed", "unknown"])

    def query_blockchain(self, transaction_id):
        # Simulate contacting the blockchain server for transaction status
        # Return a random status: confirmed or unknown
        return random.choice(["confirmed", "unknown"])

    def transactions(self):
        # TODO
        # Simulating transactions data (Replace this with actual data retrieval)
        transactions_data = [
            {
                "id": "41VYNQ3dy1dZ4vKrC1vkUT4TgjcDyaEa72yVsik2SnGZ",
                "status": "confirmed",
                "timestamp": "20231110 13:05:00.101",
                "coin": 1.0,
                "source": "8cxiskBh2AJSNefWKPQ7ErfmLoM4hs4esGq8REu63C3U",
                "destination": "HtBTNpCt5fmPrvESqVp1UFsiX5wnMCtmgt7Cxi85MFiF"
            },

        ]

        print(f"{self.get_current_date_time()} DSC v1.0")

        for idx, txn in enumerate(transactions_data, start=1):
            print(f"{self.get_current_date_time()} Transaction #{idx}: id={txn['id']}, status={txn['status']}, "
                  f"timestamp=\"{txn['timestamp']}\", coin={txn['coin']}, "
                  f"source={txn['source']}, destination={txn['destination']}")

    def print_help(self):
        print(app_info+"\nHelp menu for Wallet, supported commands:\n./dsc wallet help\n./dsc wallet create\n./dsc wallet key\n./dsc wallet balance\n./dsc wallet send <amount> <address>\n./dsc wallet transaction <ID>\n./dsc wallet transactions\n")
