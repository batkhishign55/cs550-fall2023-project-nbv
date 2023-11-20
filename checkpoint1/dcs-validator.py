import random
import string
import struct
import sys
import time
import blake3
# import metronome
import config_validator
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.job import Job
from apscheduler.triggers.interval import IntervalTrigger


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
        }
    }
}

# hash input struct - fingerprint[16], primary_key[32], nonce[int]
hash_input_struct = struct.Struct('16s 32s Q')


# blake3 hashing input data
def blake3_hash(data):
    hashed = blake3.blake3(data).hexdigest()
    return hashed


# validator usage info
def display_help():
    return f"""DSC: DataSys Coin Blockchain {validator_config['version']}
Help menu for validator, supported commands:
./dsc validator help
./dsc validator pos_check
./dsc validator"""


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
        if prefix_hash_lookup == prefix_hash_output:
            nonce = hash_input['NONCE']
            break
        else:
            hash_input['NONCE']+=1
    end_time = time.time()
    return nonce, hash_count/(end_time-start_time)

# temp code
def generate_random_block():
    letters = string.ascii_letters + string.digits  # includes both uppercase, lowercase letters, and digits
    return {'block': 'block'+letters[:10], 'diff': 30, 'hash':blake3_hash(''.join(random.choice(letters) for _ in range(10)).encode('utf-8'))}


def pow_job(fingerprint):
    #get last block hash
    last_block = generate_random_block()
    # hash_value = blake3_hash(last_block_hash['hash'])
    logger.info(f'block {last_block["block"]}, diff {last_block["diff"]}, hash {last_block["hash"]}')

    hash_input = {
    'fingerprint' : (fingerprint.encode('utf-8')).ljust(16, b'\0'), 
    'public_key' : (validator_config['validator']['public_key'].encode('utf-8')).ljust(32, b'\0'), 
    'NONCE': 0 
    }
    # difficulty_bits =  metronome.dif()
    nonce, speed = pow_lookup(hash_input, last_block, 6)
    logger.info(f'{last_block["block"]}, NONCE {nonce} ({speed:.2f} H/S)')


validator_config, err = config_validator.get_validated_fields('dsc_config.yaml', template)
if not validator_config:
    logger.error(err)
    exit(1)

fingerprint = validator_config['validator']['fingerprint']

# Log an info message
logger.info(f'DSC {validator_config["version"]}')

if validator_config['validator']['proof_pow']['enable']:
    logger.info('Proof of Work (2-threads)')
    logger.info(f'Fingerprint: {fingerprint}')
    
    # Create a scheduler object
    scheduler = BackgroundScheduler()

    # Create a trigger that runs every 6 seconds
    trigger = IntervalTrigger(seconds=6)

    # Add the job to the scheduler
    scheduler.add_job(func = pow_job, args=[fingerprint], trigger= trigger)

    # Start the scheduler
    scheduler.start()

    # Keep the program running indefinitely
    while True:
        time.sleep(1)


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "help":
        print(display_help())

# for i in range(0, 100):
#     # Generating a random string of length 10
#     random_string = generate_random_string(10)
#     # print(random_string)
#     sample_bytes = random_string.encode('utf-8')

#     # hash_lookup = "sample"
#     # hash_loopkup_encode = sample_bytes.encode('utf-8')
#     hash_value = blake3_hash(sample_bytes)

#     print(pow_lookup(hash_input, hash_value, 30, 6))

# hash_input_pom = {
#     'fingerprint' : (validator_config['validator']['fingerprint'].encode('utf-8')).ljust(16, b'\0'), 
#     'public_key' :(validator_config['validator']['public_key'].encode('utf-8')).ljust(32, b'\0'), 
#     # 'NONCE': 0 
# }

# hashes = bytearray(1000 // (24 + 8)) 
# offset = 0

# for i in range(1000 // (24 + 8)):

#   # Pack the data    
#   data = struct.pack('16s 32s Q', hash_input_pom['fingerprint'], hash_input_pom['public_key'], i) 
  
#   # Hash  
#   hash_value = blake3.blake3(data).digest()
  
#   # Truncate hash to 24 bytes
#   hash_bytes = hash_value[:24]

  
#   # Store hash and nonce
#   hashes[offset:offset+24] = hash_bytes
#   hashes[offset+24:offset+32] = struct.pack('Q', i)  
  
#   offset += 32

# print(hashes)