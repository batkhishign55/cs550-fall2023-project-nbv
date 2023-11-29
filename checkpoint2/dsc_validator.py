import logging
import queue
import random
import struct
import threading
import time
from bisect import bisect_left

import blake3
import psutil
import requests
import yaml
from bintrees import FastRBTree

import config_validator
from block import Block

# Set up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(message)s', datefmt='%Y%m%d %H:%M:%S')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# app = Flask(__name__)

# validator config template
template = {
    'version': str,
    'validator': {
        'fingerprint': str,
        'public_key': str,
        'proof_pow': {
            'enable': bool,
            'threads_hash': int
        },
        'proof_pom': {
            'enable': bool,
            'threads_hash': int,
            'memory': str
        }
    }
}

# hash input struct - fingerprint[16], primary_key[32], nonce[int]
hash_input_struct = struct.Struct('16s 32s Q')


# blake3 hashing input data
def blake3_hash(data):
    hasher = blake3.blake3()
    hasher.update(data)
    hash_result = hasher.digest(24)
    return hash_result.hex()


# validator usage info
# @app.route('/validator/help')
def display_help():
    return f"""DSC: DataSys Coin Blockchain {validator_config['version']}
Help menu for validator, supported commands:
./dsc validator help
./dsc validator pos_check
./dsc validator"""


def convert_memory(value):
    return (
        1024 if ('G' in value.upper() and 'B' in value.upper()) else
        1024 * int(value.upper().replace('G', '')) if 'G' in value.upper() else
        int(value.upper().replace('MB', '')) if 'MB' in value.upper() else
        int(value.upper().replace('M', ''))
    )


# Generate data in trie DS, data is automatically stored in sorted order. search takes K time where K is the length of lookup key(difficulty len)
def pom_write(size, fingerprint, public_key, threads):
    global data_queue
    data_queue = queue.Queue()
    global tree
    tree = FastRBTree()
    generated = False
    inserted = False

    def producer_thread(size, fingerprint, public_key, thread_i):
        logger.info(f"generating hashes [Thread #{thread_i + 1}]")
        nonce = random.randint(0, 2 ** 64 - 1)
        start_mem = psutil.Process().memory_info().rss / 1024 ** 2

        while True:
            try:
                nonce_bytes = nonce.to_bytes(8, byteorder='big')
                data = struct.Struct('16s 32s 8s').pack(fingerprint, public_key, nonce_bytes)
                hash_output = blake3_hash(data)

                # Add the data to the shared queue
                data_queue.put((hash_output, nonce))

                nonce += 1

                # Calculate the current memory usage
                current_mem = psutil.Process().memory_info().rss / 1024 ** 2

                if current_mem - start_mem > size:
                    break
            except MemoryError:
                logger.error("Out of memory. Please free up some space and retry.")
                break
        nonlocal generated
        generated = True

        logger.info(f"finished generating hashes [Thread #{thread_i + 1}, nonce = {nonce}]")

    def consumer_thread():
        logger.info("Pushing hashes to tree.")
        while not data_queue.empty():
            try:
                # Retrieve data from the shared queue
                hash_output, nonce = data_queue.get()

                # Insert the data into the FastRBTree
                tree[hash_output] = nonce
            except MemoryError:
                logger.error("Out of memory. Please free up some space and retry.")
                break
        logger.info("All hashes are moved to tree")
        nonlocal inserted
        inserted = True

    start_time = time.time()
    # Create and start producer threads
    threads_list = []
    for thread_i in range(threads):
        thread = threading.Thread(target=producer_thread, args=(size // threads, fingerprint, public_key, thread_i))
        thread.start()
        threads_list.append(thread)

    for thread in threads_list:
        thread.join()

    # Create and start the consumer thread
    consumer_thread = threading.Thread(target=consumer_thread)
    consumer_thread.start()

    # Wait for all threads to finish
    consumer_thread.join()
    if generated is True and inserted is True:
        logger.info(f"gen/org hashes ({time.time() - start_time} sec)")
        return True
    else:
        return False


def pom_lookup(hash_lookup, diff, hash_input=None):

    hash = hash_lookup['block']
    # diff = hash_lookup['diff']
    nonce = -1

    prefix_hash_lookup = hash[:diff // 5]
    start_time = time.time()
    i = bisect_left(keys, prefix_hash_lookup)
    if i < len(keys) and keys[i].startswith(prefix_hash_lookup):
        nonce = tree[keys[i]]
    return nonce, time.time() - start_time


# PoW lookup - validate hash_lookup match with hash_input, increment NONCE by 1 when match not found. Time limit - 6 seconds. 
def pow_lookup( hash_lookup, diff, hash_input):

    start_time = time.time()
    hash_count = 0
    nonce = -1
    timeout = 5
    while (time.time() - start_time) < timeout:
        data = hash_input_struct.pack(hash_input['fingerprint'], hash_input['public_key'], hash_input['NONCE'])
        hash_output = blake3_hash(data)
        hash_count += 1
        prefix_hash_output = hash_output[:diff // 5]
        prefix_hash_lookup = hash_lookup['block'][:diff // 5]
        if prefix_hash_lookup == prefix_hash_output:
            nonce = hash_input['NONCE']
            logger.info(f"Found a nonce : {nonce}")

            break
        else:
            hash_input['NONCE'] += 1

    end_time = time.time()
    # while (time.time() - start_time) < timeout:
    #     time.sleep(0.1)
    return nonce, hash_count / (end_time - start_time)


def send_to_blockchain(new_block):
    url = 'http://{0}:{1}/addblock'.format(cfg_bc['server'], cfg_bc['port'])
    x = requests.post(url, data=new_block)


def init_validator():
    global cache

    cache = []

    if len(cache) == 0:
        url = 'http://{0}:{1}/get_txn?max_txns=8191'.format(cfg_pool['server'], cfg_pool['port'])
        response = requests.post(url)
        for transaction in response.json()['submitted_txns']:
            # TODO check if transaction is valid.
            cache.append(transaction) # TODO - check this part. transactions should be added in array in block.

    # get last block hash
    lastblock_url = 'http://{0}:{1}/lastblock'.format(cfg_bc['server'], cfg_bc['port'])
    last_block = requests.get(lastblock_url)

    difficulty_url = 'http://{0}:{1}/difficulty'.format(cfg_metronome['server'], cfg_metronome['port'])
    res = requests.get(difficulty_url)
    difficulty_bits = res.json()['difficulty']
    hash_input = {
        'fingerprint': fingerprint,
        'public_key': public_key,
        'NONCE': 0
    }
    logger.info(f"diff {difficulty_bits}, hash {last_block.json()['block']}")
    nonce, speed = consensus(last_block.json(), difficulty_bits, hash_input)
    logger.info(f'{last_block.json()["block"]}, NONCE {nonce} ({speed:.2f} H/S)')
    if nonce != -1:
        block = Block(version=1, prev_block_hash=last_block.json()['block'], block_id=random.randint(0, 2 ** 32 - 1),
                      timestamp=int(time.time()), difficulty_target=difficulty_bits, nonce=nonce, transactions=[])

        # Serialize and Deserialize Block
        serialized_block = block.pack()

        send_to_blockchain(serialized_block)
        logger.info(
            f"New block created, hash {block.calculate_hash()} sent to blockchain")
        cache = None
    else:
        logger.info("Could not find a nonce")


def init():
    # global validator_config
    validator_config, err = config_validator.get_validated_fields('dsc-config.yaml', template)
    if not validator_config:
        logger.error(err)
        exit(1)

    # Log an info message
    logger.info(f'DSC {validator_config["version"]}')
    global fingerprint, public_key
    fingerprint = (validator_config['validator']['fingerprint'].encode('utf-8')).ljust(16, b'\0')
    public_key = (validator_config['validator']['public_key'].encode('utf-8')).ljust(32, b'\0')

    def load_config():
        with open("dsc-config.yaml", "r") as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                logger.error(exc)

    config = load_config()
    global cfg_pool, cfg_metronome, cfg_bc, consensus
    cfg_pool = config['pool']

    cfg_metronome = config['metronome']
    cfg_bc = config['blockchain']
    consensus = None
    if validator_config['validator']['proof_pow']['enable']:
        thread_config = validator_config["validator"]["proof_pow"]["threads_hash"]
        logger.info(f'Proof of Work ({thread_config}-threads)')
        logger.info(f'Fingerprint: {fingerprint.decode("utf-8")}')
        consensus = pow_lookup
    elif validator_config['validator']['proof_pom']['enable']:
        thread_config = validator_config["validator"]["proof_pom"]["threads_hash"]
        logger.info(f'Proof of Memory ({thread_config}-threads)')
        logger.info(f'Fingerprint: {fingerprint.decode("utf-8")}')
        mem_config = validator_config["validator"]["proof_pom"]["memory"]
        memory = convert_memory(mem_config)
        logger.info(f"gen/org {mem_config} hashes using {thread_config} passes")
        write = pom_write(memory, fingerprint, public_key, thread_config)
        if write is False:
            logger.error("Could not generate the data in memory. PoM cannot start without hashes pre-generated")
            exit(1)
        logger.info("Generated hashes of given size in memory")
        global keys
        keys = list(tree.keys())
        consensus = pom_lookup
    else:
        logger.error("Unsupported feature enabled.")
        exit(1)
    # display_help()
    # app.run(debug=True)

    while True:
        start_time = time.time()

        validation_thread = threading.Thread(target=init_validator())
        validation_thread.start()
        validation_thread.join(timeout=6)  # Timeout after 6 seconds

        end_time = time.time()
        elapsed_time = end_time - start_time

        if elapsed_time < 6:
            time.sleep(6 - elapsed_time)

    # init_validator()

