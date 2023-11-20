import datetime
import time
import base58
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
import requests

from block import Block

app_info = "DSC v1.0"

app = Flask(__name__)


@app.route('/')
def hello():
    return 'Metronome'


@app.route('/difficulty')
def dif():
    return 30


@app.route('/nonce')
def nonce():
    print("received nonce")


# print("{time.time()}")
print(datetime.datetime.now(), " ", app_info)
print(datetime.datetime.now(), " ", "Metronome started with 2 worker threads")

scheduler = BackgroundScheduler()


def send_to_blockchain(new_block):
    url = 'http://localhost:5001/addblock'
    print(new_block)
    # print(new_block.decode("utf-8"))
    x = requests.post(url, data=b"x00x00x01")


def create_block():
    block = Block(
        version=1,
        prev_block_hash="",
        block_id=1,
        timestamp=int(time.time()),
        difficulty_target=1000,
        nonce=123, transactions=[])
    new_block = block.pack()
    # to-do send to blockchain
    send_to_blockchain(new_block)
    # print(datetime.datetime.now(), " ", "New block created, hash ",
    #       base58.b58encode(new_block).decode("utf-8"), ", sent to blockchain")


scheduler.add_job(create_block, 'interval', seconds=6)
scheduler.start()
