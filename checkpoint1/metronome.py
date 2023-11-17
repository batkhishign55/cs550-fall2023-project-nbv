import threading
import datetime
import base58
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

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


def start_job():
    threading.Timer(6.0, create_block).start()


print(datetime.datetime.now(), " ", app_info)
print(datetime.datetime.now(), " ", "Metronome started with 2 worker threads")

scheduler = BackgroundScheduler()


def create_block():
    block = Block(version=1, prev_block_hash="00000000000000000000000000000000",
                  difficulty_target=1000, transactions=[])
    new_block = block.pack()
    # to-do send to blockchain
    print(datetime.datetime.now(), " ", "New block created, hash ", base58.b58encode(new_block).decode("utf-8"), ", sent to blockchain")
    


scheduler.add_job(create_block, 'interval', seconds=6)
scheduler.start()
