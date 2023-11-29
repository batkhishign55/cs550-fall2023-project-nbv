import logging
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
    x = requests.post(url, data=new_block)


def create_block():

    transaction1 = Transaction("Sender1", "Recipient1", 10.5, 1637997900, "ID1", "Signature1")
    transaction2 = Transaction("Sender2", "Recipient2", 5.0, 1637998000, "ID2", "Signature2")

    # Create Block with Transactions
    block = Block(1, "159f4ef0bcc5fa42fc90bdf7acfd7308bf9b3dacd501d23f3cff799d3f6b3234", 123, 1637998100, 3, 123456, [transaction1, transaction2])

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

scheduler.add_job(create_block, 'interval', seconds=6)
scheduler.start()
