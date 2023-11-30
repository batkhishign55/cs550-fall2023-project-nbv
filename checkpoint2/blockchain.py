import datetime
import time

import requests
from flask import Flask, request
import yaml

from block import Block, Transaction

app_info = "DSC v1.0"

app = Flask(__name__)


class Cache:
    def __init__(self):
        self.cache_dict = {}

    def lookup_in_cache(self, wallet):
        if wallet in self.cache_dict:
            return self.cache_dict[wallet]
        else:
            return (0, -1)

    def update_cache(self, wallet, balance, block_height):
        self.cache_dict[wallet] = (balance, block_height)

    def clear_cache(self):
        self.cache_dict = {}


class Blockchain:
    def __init__(self):
        self.blocks = []
        self.difficulty_bits = 30
        # self.difficulty_tracker = {'last-block': None, 'counter': 0}
        # self.consecutive_validator_blocks = 0
        # self.consecutive_metronome_blocks = 0

    def add_block(self, block):
        self.blocks.append(block)

    def get_block_length(self):
        return len(self.blocks)

    def get_last_block_hash(self):
        return self.blocks[-1].calculate_hash()

    def get_balance(self, wallet, cache_block_height, cache_bal):
        balance = cache_bal
        for block in self.blocks[cache_block_height + 1:]:
            print("searched in a block")
            for txn in block.transactions:
                if txn.recipient_address == wallet:
                    balance += txn.value
                if txn.sender_address == wallet:
                    balance -= txn.value

        return (balance, len(self.blocks) - 1)


blockchain = Blockchain()
cache = Cache()


@app.route('/')
def hello():
    return 'Blockchain'


@app.post('/addblock')
def addblock():
    block = Block.unpack(request.data)
    # if blockchain.get_last_block_hash() == block.prev_block_hash:
    blockchain.add_block(block)
    blockchain.difficulty_tracker = {'last-block': block.prev_block_hash, 'counter': 1}
    print(f"The block is {block.block_id, block.nonce, block.timestamp, block.transactions}")
    print(f"Sending below transactions to cleanup {block.transactions}")
    url = 'http://{0}:{1}/confirmed_transactions'.format(
        cfg_pool['server'], cfg_pool['port'])

    x = requests.post(url, data=request.data)
    received_from = "metronome"
    if len(block.transactions) != 0:
        received_from = "validator"
    print(datetime.datetime.now(
    ), f" New block received from {received_from}, Block hash {block.calculate_hash()}")
    # elif blockchain.difficulty_tracker['last-block'] != block.prev_block_hash:
    #     blockchain.difficulty_tracker['counter'] += 1

    return {"message": "success"}


# curl localhost:10002/lastblock
@app.get('/lastblock')
def lastblock():
    return {"block": blockchain.get_last_block_hash(), "block_id": blockchain.get_block_length()}


# curl "localhost:10002/balance?wallet=Hje7meKmLgEAZBBTSRP9ZQmnwhPuL7N4G5kFq52qu6mt"
@app.get('/balance')
def balance():
    (cache_bal, cache_block_height) = cache.lookup_in_cache(
        request.args["wallet"])

    (balance, block_height) = blockchain.get_balance(
        request.args["wallet"], cache_block_height, cache_bal)

    if (cache_block_height != block_height):
        print(request.args["wallet"], balance, block_height)
        cache.update_cache(request.args["wallet"], balance, block_height)

    print(datetime.datetime.now(), " Balance request for " +
          request.args["wallet"] + ", " + str(balance) + " coins")
    return {"balance": balance}


# curl "localhost:10002/cache"
@app.get('/cache')
def get_cache():
    print(cache.__dict__)
    return {"message": "success"}


# curl "localhost:10002/txn?id=some-txn-id"
@app.get('/txn')
def transaction():
    print(datetime.datetime.now(), " Transaction request status for " +
          request.args["id"] + ", unkhown")
    return "unknown"


# curl "localhost:10002/txns?ids=id1,id2,id3"
@app.get('/txns')
def transactions():
    print(datetime.datetime.now(), " Transactions request for " +
          request.args["ids"] + ", none found")
    return "none found"


@app.get('/difficulty')
def difficulty():
    # if blockchain.difficulty_tracker['counter'] > 0.75 * validator_instances:
    #     blockchain.difficulty_bits += 1
    # elif blockchain.difficulty_tracker['counter'] < 0.25 * validator_instances:
    #     blockchain.difficulty_bits -= 1
    return {"difficulty_bits": blockchain.difficulty_bits}


def load_config():
    with open("dsc-config.yaml", "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


def create_genesis_block():
    transaction1 = Transaction(sender_address="", recipient_address="Hje7meKmLgEAZBBTSRP9ZQmnwhPuL7N4G5kFq52qu6mt", value=1000, timestamp=int(
        time.time()), transaction_id="ID1", signature="Signature1")
    block = Block(version=2, prev_block_hash="0", block_id=0, timestamp=int(
        time.time()), difficulty_target=30, nonce=123456, transactions=[transaction1])

    blockchain.add_block(block)


config = load_config()
print(datetime.datetime.now(), " DSC " + str(config["version"]))
print(datetime.datetime.now(), " Blockchain server started with 2 worker threads")
difficulty_bits = 30
create_genesis_block()
cfg_pool = config['pool']
validator_instances = config['validator']['instances']
