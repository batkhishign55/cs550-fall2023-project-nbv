import logging
import threading
import datetime
import time
import base58
import requests
import yaml
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
import config_validator
from block import Block


# Set up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s.%(msecs)03d %(message)s', datefmt='%Y%m%d %H:%M:%S')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# metronome config template
template = {
    'version': str,
    'metronome': {
        'server': str,
        'port': int,
        'threads': int
    }
}

validator_config, err = config_validator.get_validated_fields(
    'dsc-config.yaml', template)
if not validator_config:
    logger.error(err)
    exit(1)

app_info = f"DSC {validator_config['version']}"
app = Flask(__name__)


@app.route('/')
def hello():
    return 'Metronome'


@app.route('/difficulty')
def dif():
    return 30


@app.route('/nonce')
def nonce():
    logger.info("received nonce")


def load_config():
    with open("dsc-config.yaml", "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


config = load_config()
cfg_bc = config['blockchain']
logger.info(f'{app_info}')
logger.info(
    f"Metronome started with {validator_config['metronome']['threads']} worker threads")

scheduler = BackgroundScheduler()


def send_to_blockchain(new_block):
    url = 'http://{0}:{1}/addblock'.format(cfg_bc['server'], cfg_bc['port'])
    # print(new_block.decode("utf-8"))
    x = requests.post(url, data=base58.b58encode(new_block).decode('utf-8'))


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
    logger.info(
        f"New block created, hash {base58.b58encode(new_block).decode('utf-8')} sent to blockchain")


scheduler.add_job(create_block, 'interval', seconds=6)
scheduler.start()
