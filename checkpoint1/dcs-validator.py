# example of proof-of-work algorithm
import hashlib
import struct
import sys
import time
import blake3

import yaml
import config_validator

# Define the template of the desired structure
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

validator_config, err = config_validator.get_validated_fields('dsc_config.yaml', template)
if not validator_config:
    print(err)
    exit(1)


def blake3_hash(data):
    hashed = blake3.blake3(data).hexdigest()
    return hashed


def display_help():
    return f"""DSC: DataSys Coin Blockchain {validator_config['version']}
Help menu for validator, supported commands:
./dsc validator help
./dsc validator pos_check
./dsc validator"""

# TODO - Start PoW, PoM, PoS based on enable flag in config. 

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "help":
        print(display_help())
    

hash_input = {
    'fingerprint' : (validator_config['validator']['fingerprint'].encode('utf-8')).ljust(16, b'\0'), 
    'public_key' :(validator_config['validator']['public_key'].encode('utf-8')).ljust(32, b'\0'), 
    'NONCE': 0 
}
difficulty_bits = 30
hash_input_struct = struct.Struct('16s 32s Q')

def pow_lookup(hash_input, hash_lookup, difficulty, block_time):
    start_time = time.time()
    while (time.time() - start_time) < block_time:
        data = hash_input_struct.pack(hash_input['fingerprint'], hash_input['public_key'], hash_input['NONCE'])
        hash_output = blake3_hash(data)
        prefix_hash_output = hash_output[:difficulty]
        prefix_hash_lookup = hash_lookup[:difficulty]
        if prefix_hash_lookup == prefix_hash_output:
            return hash_input['NONCE']
        else:
            hash_input['NONCE']+=1

    return -1

hash_lookup = blake3_hash(b'sample')

print(pow_lookup(hash_input, hash_lookup, 30, 6))