import datetime
from flask import Flask, request
import yaml

app_info = "DSC v1.0"
blockchain = None

app = Flask(__name__)


class Block:
    def __init__(self, data):
        self.data = data

    def get_data(self):
        return self.data


class Blockchain:
    def __init__(self):
        self.blocks = []

    def add_block(self, data):
        new_block = Block(data)
        self.blocks.append(new_block)

    def print_blocks(self):
        for block in self.blocks:
            print(block.data)

    def get_block_length(self):
        return len(self.blocks)

    def get_last_block(self):
        return self.blocks[-1].get_data()


@app.route('/')
def hello():
    return 'Blockchain'


@app.post('/addblock')
def addblock():
    blockchain.add_block(request.data.decode('utf-8')   )
    print(datetime.datetime.now(
    ), " New block received from metronome, Block hash " + request.data.decode('utf-8'))
    return {"message": "success"}


# curl localhost:10002/lastblock
@app.get('/lastblock')
def lastblock():
    return {"block": blockchain.get_last_block(), "block_id": blockchain.get_block_length()}


# curl "localhost:10002/balance?wallet=some-address"
@app.get('/balance')
def balance():
    print(datetime.datetime.now(), " Balance request for " +
          request.args["wallet"] + ", " + str(float(0)) + " coins")
    return "0"


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


blockchain = Blockchain()


def load_config():
    with open("dsc-config.yaml", "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


config = load_config()
print(datetime.datetime.now(), " DSC " + config["version"])
print(datetime.datetime.now(), " Blockchain server started with 2 worker threads")
