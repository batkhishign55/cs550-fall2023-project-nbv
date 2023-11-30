import json
import logging
import random
import base58

from flask import Flask, request
import yaml
import base58
import yaml
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec

# Set up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s.%(msecs)03d %(message)s', datefmt='%Y%m%d %H:%M:%S')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

app = Flask(__name__)

# In-memory databases for unconfirmed and submitted transactions
unconfirmed_transactions = {}
submitted_transactions = {}


def validate_transaction_data(data):
    # Check if all required keys are present
    required_keys = ['sender_public_address', 'recipient_public_address', 'value', 'timestamp', 'transaction_id',
                     'signature']
    if not all(key in data for key in required_keys):
        return False

    # Check the length of each attribute
    if (
            len(data['sender']) == 32 and
            len(data['recipient']) == 32 and
            isinstance(data['value'], float) and
            isinstance(data['timestamp'], int) and
            len(data['txn_id']) == 16 and
            len(data['signature']) == 32
    ):
        return True

    return False


@app.route('/')
def hello():
    return 'Pool'


@app.post('/confirmed_transactions')
def cleanup_confirmed_transactions():
    # logger.info(f'confirmed transactions clean up in progress')
    # call blockchain's unpack to unpack inputted block and retrieve transactions.
    transactions = request.data
    # tx_ids = list(transactions.keys())
    for transaction in transactions:
        submitted_transactions.pop(transaction.transaction_id)
    return {"Status": "OK"}


@app.get('/transaction_status')
def transaction_status():
    transaction_id = request.args.get('txn_id')
    if transaction_id in submitted_transactions:
        return {"status": "Submitted"}
    elif transaction_id in unconfirmed_transactions:
        return {"status": "Unconfirmed"}
    else:
        return {"status": "Unknown"}


@app.post('/get_txn')  # Provides valid transactions to validators
def get_transactions():
    num_transactions = request.args.get('max_txns')
    tx_ids = list(unconfirmed_transactions.keys())
    # Add only if it is valid transaction - Todo call blockchain's method before adding in submitted transactions.
    for _ in range(int(num_transactions)):
        if tx_ids:
            tx_id = random.choice(tx_ids)
            tx = unconfirmed_transactions.pop(tx_id)
            submitted_transactions[tx_id] = tx
    return {"submitted_txns": submitted_transactions}


def verify_signature(message, signature, public_key_string):

    public_key_bytes = base58.b58decode(public_key_string)

    public_key = serialization.load_pem_public_key(
        public_key_bytes,
        backend=default_backend()
    )
    try:
        signature_bytes = base58.b58decode(signature)
        public_key.verify(
            signature_bytes,
            message.encode('utf-8'),
            ec.ECDSA(hashes.SHA256())
        )
        return True
    except Exception:
        return False


@app.post('/receive_txn')
def receive_txn():
    data = request.get_json()
    is_verified = verify_signature(
        data['message'], data['signature'], data['public_key'])

    if is_verified:
        print("Signature verified. The message is authentic.")
    else:
        print("Signature verification failed. The message may be tampered.")
        return "Bad request", 400
    message = json.loads(data['message'])

    unconfirmed_transactions[message['txn_id']] = message
    logger.info(
        f"Transaction {message['txn_id']} received from {message['sender']}, ACK")
    return {"message": "acknowledged"}


def load_config():
    with open("dsc-config.yaml", "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


config = load_config()
logger.info(f"DSC {config['version']}")
logger.info("Pool started with 4 worker threads")  # TODO
