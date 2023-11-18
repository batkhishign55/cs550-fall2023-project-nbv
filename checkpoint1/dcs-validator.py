# example of proof-of-work algorithm
import hashlib
import sys
import time

import yaml
import config_validator

# Define the template of the desired structure
template = {
    'validator': {
        'fingerprint': str,
        'public_key': str,
        'proof_pow': {
            'enable': bool,
            'threads_hash': int
        }
    }
}

if not config_validator.validate(template):
    exit(1)

with open('dsc_config.yaml', 'r') as file:
    config = yaml.safe_load(file)

version = config['version']

def display_help():
    return f"""DSC: DataSys Coin Blockchain {version}
Help menu for validator, supported commands:
./dsc validator help
./dsc validator pos_check
./dsc validator"""


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "help":
        print(display_help())
        

max_nonce = 2 ** 32 # 4 billion

def proof_of_work(header, difficulty_bits):
    # calculate the difficulty target
    target = 2 ** (256-difficulty_bits)
    for nonce in range(max_nonce):
        hash_result = hashlib.sha256((str(header)+str(nonce)).encode()).hexdigest()
        # check if this is a valid result, below the target
        if int(hash_result, 16) < target:
            print(f"Success with nonce {nonce}")
            print(f"Hash is {hash_result}")
            return (hash_result,nonce)
    print(f"Failed after {nonce} (max_nonce) tries")
    return nonce


if __name__ == '__main__':
    nonce = 0
    hash_result = ''
    # difficulty from 0 to 31 bits
    difficulty_bits = 30
    
    difficulty = 2 ** difficulty_bits
    print(f"Difficulty: {difficulty} ({difficulty_bits} bits)")
    print(f"Starting search...")
    # checkpoint the current time
    start_time = time.time()
    # make a new block which includes the hash from the previous block
    # we fake a block of transactions - just a string
    new_block = 'test block with transactions' + hash_result
    # find a valid nonce for the new block
    (hash_result, nonce) = proof_of_work(new_block, difficulty_bits)
    # checkpoint how long it took to find a result
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed Time: {elapsed_time} seconds")
    if elapsed_time > 0:
        # estimate the hashes per second
        hash_power = float((nonce)/elapsed_time)
        print(f"Hashing Power: {hash_power} hashes per second")