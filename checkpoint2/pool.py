import datetime
import logging
import random
from collections import deque

import jsonify
from flask import Flask, request
import yaml

# Set up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(message)s', datefmt='%Y%m%d %H:%M:%S')

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
            len(data['sender_public_address']) == 32 and
            len(data['recipient_public_address']) == 32 and
            isinstance(data['value'], float) and
            isinstance(data['timestamp'], int) and
            len(data['transaction_id']) == 16 and
            len(data['signature']) == 32
    ):
        return True

    return False


@app.route('/')
def hello():
    return 'Pool'

@app.post('/confimed_transactions')
def cleanup_confirmed_transactions():
    # call blockchain's unpack to unpack inputted block and retrieve transactions.
    block = request.args.get('block')
    transactions = {} #dummy
    #assume transactions list
    tx_ids = list(transactions.keys())
    for t_id in tx_ids:
        submitted_transactions.pop(t_id)

@app.get('/transaction_status')
def transaction_status():
    transaction_id = request.args.get('transaction_id')
    if transaction_id in submitted_transactions:
        return "Submitted"
    elif transaction_id in unconfirmed_transactions:
        return "Unconfirmed"
    else:
        return "Unknown"


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


@app.post('/receive_txn')
def receive_txn():
    data = request.get_json()
    transaction_id = data.get('transaction_id')
    transaction_object = data.get('transaction_object')
    if validate_transaction_data(transaction_object):
        # Store transaction in unconfirmed transactions database
        unconfirmed_transactions[transaction_id] = transaction_object
        # Print transaction in console
        logger.info(f"Transaction {transaction_id} received from {transaction_object['source']}, ACK")
        return "Accepted"

    else:
        return "Bad Request"


def load_config():
    with open("dsc-config.yaml", "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


config = load_config()
logger.info(f"DSC {config['version']}")
logger.info("Pool started with 4 worker threads")  # TODO
