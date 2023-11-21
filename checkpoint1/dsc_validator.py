import logging
import queue
import random
import string
import struct
import sys
import threading
import time
from bisect import bisect_left

import blake3
import psutil
from apscheduler.job import Job
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from bintrees import FastRBTree

import config_validator

# Set up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(message)s', datefmt='%Y%m%d %H:%M:%S')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


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
def display_help():
    return f"""DSC: DataSys Coin Blockchain {config_validator['version']}
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

    def producer_thread(size, fingerprint, public_key, thread_i):
        logger.info(f"generating hashes [Thread #{thread_i+1}]")
        nonce = random.randint(0, 2**64 - 1)
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

        logger.info(f"finished generating hashes [Thread #{thread_i+1}, nonce = {nonce}]")
        

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
    start_time = time.time()
    # Create and start producer threads
    threads_list = []
    for thread_i in range(threads):
        
        thread = threading.Thread(target=producer_thread, args=(size//threads, fingerprint, public_key, thread_i))
        thread.start()
        threads_list.append(thread)
    
    for thread in threads_list:
        thread.join()

    # Create and start the consumer thread
    consumer_thread = threading.Thread(target=consumer_thread)
    consumer_thread.start()

    # Wait for all threads to finish
    consumer_thread.join()
    
    logger.info(f"gen/org hashes ({time.time()-start_time} sec)")
   

def pom_lookup(hash_lookup, max_time):
    hash = hash_lookup['hash']
    diff = hash_lookup['diff']
    nonce = -1
    prefix_hash_lookup = hash[:diff//5]
    start_time = time.time()
    i = bisect_left(keys, prefix_hash_lookup) 
    if i<len(keys) and keys[i].startswith(prefix_hash_lookup):
        nonce = tree[keys[i]]
    while (time.time() - start_time) < max_time:
        time.sleep(0.1)
    return nonce
    
# PoW lookup - validate hash_lookup match with hash_input, increment NONCE by 1 when match not found. Time limit - 6 seconds. 
def pow_lookup(hash_input, hash_lookup, block_time):
    diff = int(hash_lookup['diff'])
    start_time = time.time()
    hash_count = 0
    nonce = -1
    while (time.time() - start_time) < block_time:
        data = hash_input_struct.pack(hash_input['fingerprint'], hash_input['public_key'], hash_input['NONCE'])
        hash_output = blake3_hash(data)
        hash_count+=1
        prefix_hash_output = hash_output[:diff//5]
        prefix_hash_lookup = hash_lookup['hash'][:diff//5]
        # print(f'Comparing {prefix_hash_output, prefix_hash_lookup}')
        if prefix_hash_lookup == prefix_hash_output:
            nonce = hash_input['NONCE']
        else:
            hash_input['NONCE']+=1
    
    end_time = time.time()
    while (time.time() - start_time) < block_time:
        time.sleep(0.1)
    return nonce, hash_count/(end_time-start_time)

# temp code
def generate_random_block():
    letters = string.ascii_letters + string.digits  # includes both uppercase, lowercase letters, and digits
    return {'block': 'block'+letters[:10], 'diff': 30, 'hash':blake3.blake3(''.join(random.choice(letters) for _ in range(10)).encode('utf-8')).hexdigest()}


def pow_job(fingerprint, public_key):
    #get last block hash
    last_block = generate_random_block() #blockchain.lastblock()
    # hash_value = blake3_hash(last_block_hash['hash'])
    logger.info(f'block {last_block["block"]}, diff {last_block["diff"]}, hash {last_block["hash"]}')

    hash_input = {
    'fingerprint' : fingerprint, 
    'public_key' : public_key, 
    'NONCE': 0 
    }
    difficulty_bits =  30
    nonce, speed = pow_lookup(hash_input, last_block, difficulty_bits//5)
    logger.info(f'{last_block["block"]}, NONCE {nonce} ({speed:.2f} H/S)')

def pom_job():
    #get last block hash
    last_block = generate_random_block()
    # hash_value = blake3_hash(last_block_hash['hash'])
    logger.info(f'block {last_block["block"]}, diff {last_block["diff"]}, hash {last_block["hash"]}')

    difficulty_bits =  30
    nonce = pom_lookup(last_block, difficulty_bits//5)
    logger.info(f'{last_block["block"]}, NONCE {nonce}')


def init_validator():

    validator_config, err = config_validator.get_validated_fields('dsc-config.yaml', template)
    if not validator_config:
        logger.error(err)
        exit(1)

    fingerprint = (validator_config['validator']['fingerprint'].encode('utf-8')).ljust(16, b'\0')
    public_key = (validator_config['validator']['public_key'].encode('utf-8')).ljust(32, b'\0')
    # Log an info message
    logger.info(f'DSC {validator_config["version"]}')
     # Create a scheduler object
    scheduler = BackgroundScheduler()

    # Create a trigger that runs every 6 seconds
    trigger = IntervalTrigger(seconds=7)

    if validator_config['validator']['proof_pow']['enable']:
        logger.info(f'Proof of Work ({validator_config["validator"]["proof_pow"]["threads_hash"]}-threads)')
        logger.info(f'Fingerprint: {fingerprint.decode("utf-8")}')
        # Add the job to the scheduler
        scheduler.add_job(func = pow_job, args=[fingerprint, public_key], trigger= trigger)
        # Start the scheduler
        scheduler.start()

    elif validator_config['validator']['proof_pom']['enable']:
        thread_config = validator_config["validator"]["proof_pom"]["threads_hash"]
        mem_config = validator_config["validator"]["proof_pom"]["memory"]

        logger.info(f'Proof of Memory ({thread_config}-threads)')
        logger.info(f'Fingerprint: {fingerprint.decode("utf-8")}')
        memory = convert_memory(mem_config)
        logger.info(f"gen/org {mem_config} hashes using {thread_config} passes")
        generated = pom_write(memory, fingerprint, public_key, thread_config)
        if generated is False:
            logger.error("Could not generate the data in memory. PoM cannot start without hashes pre-generated")
            exit(1)
        logger.info("Generated hashes of given size in memory")
        global keys 
        keys = list(tree.keys())    
        # Add the job to the scheduler
        scheduler.add_job(func = pom_job, trigger= trigger)
        # Start the scheduler
        scheduler.start()
    else:
        logger.error("Unsupported feature enabled.")
    # Keep the program running indefinitely
    while True:
        time.sleep(1)


# init_validator()
if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "help":
        print(display_help())
