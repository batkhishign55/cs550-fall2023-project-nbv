
import json
import uuid
import base58
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
import datetime
import random

import requests
import yaml

app_info = "DSC: DataSys Coin Blockchain v1.0"


def load_config():
    with open("dsc-config.yaml", "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


config = load_config()
cfg_bc = config['blockchain']
cfg_p = config['pool']


class Wallet:
    def __init__(self):
        self.public_key = None
        self.private_key = None
        self.load_keys_from_yaml()

    def get_current_date_time(self):
        return datetime.datetime.now().strftime("%Y%m%d %H:%M:%S.%f")

    def generate_key_pair(self):
        private_key = ec.generate_private_key(
            ec.SECP256R1(), default_backend())
        public_key = private_key.public_key()
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self.private_key = base58.b58encode(private_key_bytes).decode('utf-8')
        self.public_key = base58.b58encode(public_key_bytes).decode('utf-8')

    def save_keys_to_yaml(self):

        keys_data = {
            'private_key': self.private_key,
            'public_key': self.public_key
        }

        with open("dsc-key.yaml", 'w') as file:
            yaml.dump(keys_data, file)

    def convert_to_key_objects(self):

        private_key_bytes = base58.b58decode(self.private_key)
        public_key_bytes = base58.b58decode(self.public_key)
        private_key = serialization.load_pem_private_key(
            private_key_bytes,
            password=None,
            backend=default_backend()
        )

        public_key = serialization.load_pem_public_key(
            public_key_bytes,
            backend=default_backend()
        )
        return private_key, public_key

    def load_keys_from_yaml(self):
        with open("dsc-key.yaml", 'r') as file:
            keys_data = yaml.safe_load(file)
        self.private_key = keys_data['private_key']
        self.public_key = keys_data['public_key']

    def sign_message(self, message):
        private_key, public_key = self.convert_to_key_objects()
        signature = private_key.sign(
            message.encode('utf-8'),
            ec.ECDSA(hashes.SHA256())
        )
        return base58.b58encode(signature).decode('utf-8')

    def verify_signature(self, message, signature):
        try:
            signature_bytes = base58.b58decode(signature)
            self.public_key.verify(
                signature_bytes,
                message.encode('utf-8'),
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except Exception:
            return False

    def create_wallet(self):
        # Generate keys
        self.generate_key_pair()

        # Save keys to YAML file
        self.save_keys_to_yaml()

    def print_keys(self):
        if hasattr(self, 'public_key'):
            print(f"{self.get_current_date_time()} DSC v1.0\n{self.get_current_date_time()} Reading dsc_config.yaml and dsc-key.yaml...\n{self.get_current_date_time()} DSC Public Address: {self.public_key}\n{self.get_current_date_time()} DSC Private Address: {self.private_key}")

        else:
            print(f"{self.get_current_date_time()} DSC v1.0\n{self.get_current_date_time()} Error in finding key information, ensure that dsc_config.yaml and dsc-key.yaml exist and that they contain the correct information. You may need to run “./dsc wallet create”")

    def get_balance(self):
        url = 'http://{0}:{1}/balance?wallet={2}'.format(
            cfg_bc['server'], cfg_bc['port'], self.public_key)
        res = requests.get(url)
        print(
            f"{self.get_current_date_time()} DSC v1.0\n{self.get_current_date_time()} DSC Wallet balance: {res.json()['balance']} coins at block x")

    def send_coins(self, value, recipient):

        transaction_id = self.generate_transaction_id()

        data = {'txn_id': str(transaction_id), 'sender': self.public_key,
                'recipient': recipient, 'value': value}
        message = json.dumps(data, indent=2)
        # Sign the message with the private key
        signature = self.sign_message(message)

        url = 'http://{0}:{1}/receive_txn'.format(
            cfg_p['server'], cfg_p['port'])
        res = requests.post(url, json={
                            'message': message, 'signature': signature, 'public_key': self.public_key})

        print(
            f"{self.get_current_date_time()} Created transaction {transaction_id}, Sending {value} coins to {recipient}")
        if res.status_code == 200:
            print(
                f"{self.get_current_date_time()} Transaction {transaction_id} submitted to pool")
        else:
            print(f"{res.status_code} {res.text}")

    def generate_transaction_id(self):
        # Generate a random transaction ID
        return uuid.uuid4()
        # return ''.join(random.choices('0123456789ABCDEF', k=16))

    def check_transaction_status(self, txn_id):

        url = 'http://{0}:{1}/transaction_status?txn_id={2}'.format(
            cfg_p['server'], cfg_p['port'], txn_id)
        res = requests.get(url)
        print(res.json())

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
