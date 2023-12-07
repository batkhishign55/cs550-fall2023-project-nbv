import datetime
import json
import logging
import time
import datetime
from urllib import request

import requests
import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request

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
    logger.info('Received an ACK from validator upon block creation')
    return {'received': 'OK'}


@app.route('/register_validator', methods=['POST'])
def register_validator():
    validator_ip = request.json.get('validator_ip')
    validator_port = request.json.get('validator_port')

    if not all([validator_ip, validator_port]):
        return {'error': 'Incomplete validator details'}, 400

    if validator_ip in registered_validators:
        return {'error': 'Validator already registered'}, 400

    registered_validators[validator_ip] = {
        'validator_ip': validator_ip,
        'validator_port': validator_port,
        'subscribed_on': datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    }

    return {'message': 'Validator registered successfully'}, 200


@app.route('/registered_validators')
def get_registered_validators():
    return json.dumps(registered_validators, indent=4)


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

@app.route('/get_metronome_info')
def get_metronome_info():
    # Placeholder values, needs to be replaced 
    num_validators = 50
    hashes_per_sec = 500
    total_hashes_stored = 10000

    return {
        "validators": num_validators,
        "hashes_per_sec": hashes_per_sec,
        "total_hashes_stored": total_hashes_stored
    }

def watcher():
    timeout_duration = 6
    start_time = time.time()
    global ack_received
    ack_received = False
    time.sleep(timeout_duration)
    if not ack_received:
        create_block()


scheduler.add_job(watcher, 'interval', seconds=7)
scheduler.start()

registered_validators = {}
