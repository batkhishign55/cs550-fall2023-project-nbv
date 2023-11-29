import logging
import time
import requests
import yaml
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from block import Block, Transaction
import config_validator

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

ack_received = False

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
    url = 'http://{0}:{1}/difficulty'.format(cfg_bc['server'], cfg_bc['port'])
    response = requests.get(url)
    difficulty = response.json()['difficulty_bits']
    return {'difficulty': difficulty}


@app.route('/block/ack')
def block_ack():
    global ack_received
    ack_received = True
    print(f'Received an ACK from validator upon block creation')
    return {'received': 'OK'}

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
    x = requests.post(url, data=new_block)


def create_block():
    # get last block hash
    url = 'http://{0}:{1}/lastblock'.format(cfg_bc['server'], cfg_bc['port'])
    res = requests.get(url)

    block = Block(version=int(config["version"]), prev_block_hash=res.json()['block'], block_id=res.json()['block_id'],
                  timestamp=int(
                      time.time()), difficulty_target=30, nonce=123456, transactions=[])

    # Serialize and Deserialize Block
    serialized_block = block.pack()

    send_to_blockchain(serialized_block)
    logger.info(
        f"New block created, hash {block.calculate_hash()} sent to blockchain")


def watcher():
    timeout_duration = 6
    start_time = time.time()
    ack_received = False
    while time.time() - start_time < timeout_duration:
        if ack_received:  # will be true if validator ack's
            time.sleep(timeout_duration - time.time() - start_time)
    if not ack_received:
        create_block()

scheduler.add_job(watcher, 'interval', seconds=7)
scheduler.start()
