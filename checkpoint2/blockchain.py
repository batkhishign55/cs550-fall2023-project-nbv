import datetime
import time
from flask import Flask, request
import yaml

from block import Block, Transaction

app_info = "DSC v1.0"

app = Flask(__name__)


class Blockchain:
    def __init__(self):
        self.blocks = []

    def add_block(self, block):
        self.blocks.append(block)

    def print_blocks(self):
        for block in self.blocks:
            print(block.data)

    def get_block_length(self):
        return len(self.blocks)

    def get_last_block_hash(self):
        return self.blocks[-1].calculate_hash()

    def get_balance(self, wallet):
        balance = 0
        for block in self.blocks:
            for txn in block.transactions:
                if txn.recipient_address == wallet:
                    balance += txn.value
                if txn.sender_address == wallet:
                    balance -= txn.value
        return balance


blockchain = Blockchain()


@app.route('/')
def hello():
    return 'Blockchain'


@app.post('/addblock')
def addblock():
    block = Block.unpack(request.data)
    blockchain.add_block(block)
    print(datetime.datetime.now(
    ), f" New block received from metronome, Block hash {block.calculate_hash()}")
    return {"message": "success"}


# curl localhost:10002/lastblock
@app.get('/lastblock')
def lastblock():
    return {"block": blockchain.get_last_block_hash(), "block_id": blockchain.get_block_length()}


# curl "localhost:10002/balance?wallet=Recipient1"
@app.get('/balance')
def balance():
    balance = blockchain.get_balance(request.args["wallet"])
    print(datetime.datetime.now(), " Balance request for " +
          request.args["wallet"] + ", " + str(balance) + " coins")
    return {"balance": balance}


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


def load_config():
    with open("dsc-config.yaml", "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


def create_genesis_block():

    transaction1 = Transaction(sender_address="dummy1", recipient_address="dummy2", value=1000, timestamp=int(
        time.time()), transaction_id="ID1", signature="Signature1")
    block = Block(version=config["version"], prev_block_hash="0", block_id=-1, timestamp=int(
        time.time()), difficulty_target=30, nonce=123456, transactions=[transaction1])
    print(block.__dict__)

    blockchain.add_block(block)


config = load_config()
print(datetime.datetime.now(), " DSC " + config["version"])
print(datetime.datetime.now(), " Blockchain server started with 2 worker threads")

create_genesis_block()
