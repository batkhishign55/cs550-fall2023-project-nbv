import json
import logging
import random
import time
import base58

from flask import Flask, request
import requests
import yaml
import base58
import yaml
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec

from block import Block, Transaction

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


@app.route('/')
def hello():
    return 'Pool'


@app.post('/confirmed_transactions')
def cleanup_confirmed_transactions():

    block = Block.unpack(request.data)
    # logger.info(f'confirmed transactions clean up in progress')
    # call blockchain's unpack to unpack inputted block and retrieve transactions.
    # transactions = request.data
    # tx_ids = list(transactions.keys())
    for transaction in block.transactions:
        print(transaction.transaction_id)
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
    num_transactions = len(unconfirmed_transactions) if int(request.args.get(
        'max_txns')) > len(unconfirmed_transactions) else int(request.args.get('max_txns'))
    # print(f"Total unconfirmed instances before deletion= {len(unconfirmed_transactions)}")

    # Add only if it is valid transaction - Todo call blockchain's method before adding in submitted transactions.
    txn_ids = list(unconfirmed_transactions)[:num_transactions]
    transactions = {txn_id: unconfirmed_transactions[txn_id] for txn_id in txn_ids}
    for txn_id in txn_ids:
        del unconfirmed_transactions[txn_id]
    # print(f"Total unconfirmed instances after deletion = {len(unconfirmed_transactions)}")
    submitted_transactions.update(transactions)
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


def validate_transaction(message, public_key):
    if message['sender'] != public_key:
        raise Exception("sender is not the owner")

    url = 'http://{0}:{1}/balance?wallet={2}'.format(
        cfg_bc['server'], cfg_bc['port'], public_key)
    res = requests.get(url)

    if res.json()['balance'] < message['value']:
        raise Exception("insufficient funds")


@app.post('/receive_txn')
def receive_txn():
    data = request.get_json()
    is_verified = verify_signature(
        data['message'], data['signature'], data['public_key'])

    if is_verified:
        print("Signature verified.")
    else:
        print("Signature verification failed")
        return "Signature verification failed", 400
    message = json.loads(data['message'])

    try:
        validate_transaction(message, data['public_key'])
    except Exception as e:
        print(str(e))
        return str(e), 400

    message['timestamp'] = int(time.time())
    message['signature'] = data['signature']

    unconfirmed_transactions[message['txn_id']] = message
    logger.info(
        f"Transaction {message['txn_id']} received from {message['sender']}, ACK")
    return {"message": "acknowledged"}

@app.route('/transactions_statistics')
def get_transactions_statistics():
    submitted_count = len(submitted_transactions)
    unconfirmed_count = len(unconfirmed_transactions)
    return {"submitted_transactions": submitted_count, "unconfirmed_transactions": unconfirmed_count}


def load_config():
    with open("dsc-config.yaml", "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


config = load_config()
cfg_bc = config['blockchain']
logger.info(f"DSC {config['version']}")
logger.info("Pool started with 4 worker threads")  # TODO
