import datetime
from flask import Flask, request

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

    def get_last_block(self):
        return self.blocks[-1].get_data()


@app.route('/')
def hello():
    return 'Blockchain'


@app.post('/addblock')
def addblock():
    blockchain.add_block(request.data)
    print(datetime.datetime.now(), " New block received from metronome, Block hash " + request.data.decode('utf-8'))
    return {"message": "success"}


@app.get('/lastblock')
def lastblock():
    return blockchain.get_last_block()


@app.get('/balance')
def balance():
    print(datetime.datetime.now(), " Balance request for " + request.args["wallet"] + ", " + str(float(0)) + " coins")
    return "0"


@app.get('/txn')
def transaction():
    print(datetime.datetime.now(), " Transaction request status for " + request.args["id"] + ", unkhown")
    return "unknown"


@app.get('/txns')
def transactions():
    print(datetime.datetime.now(), " Transactions request for " + request.args["ids"] + ", none found")
    return "none found"

blockchain = Blockchain()

print(datetime.datetime.now(), " ", app_info)
print(datetime.datetime.now(), " ", "Blockchain server started with 2 worker threads")

