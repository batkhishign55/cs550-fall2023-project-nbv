import logging
import threading
import datetime
import time
import base58
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
import config_validator
from block import Block


# Set up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(message)s', datefmt='%Y%m%d %H:%M:%S')

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

validator_config, err = config_validator.get_validated_fields('dsc_config.yaml', template)
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


def start_job():
    threading.Timer(6.0, create_block).start()


logger.info(f'{app_info}')
logger.info(f"Metronome started with {validator_config['metronome']['threads']} worker threads")

scheduler = BackgroundScheduler()


def create_block():
    block = Block(version=1, prev_block_hash="00000000000000000000000000000000",
                  difficulty_target=1000, transactions=[])
    new_block = block.pack()
    # to-do send to blockchain
    logger.info(f"New block created, hash {base58.b58encode(new_block).decode('utf-8')} sent to blockchain")
    


scheduler.add_job(create_block, 'interval', seconds=6)
scheduler.start()
