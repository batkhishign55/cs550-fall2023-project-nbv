import requests
import json



num_submitted_transactions =0
num_unconfirmed_transactions =0

class Monitor:
    def __init__(self):
        self.blockchain_url = 'http://{0}:{1}'.format(cfg_bc['server'], cfg_bc['port'])
        self.pool_url = 'http://{0}:{1}'.format(cfg_bc['server'], cfg_bc['port'])
        self.metronome_url = 'http://{0}:{1}'.format(cfg_bc['server'], cfg_bc['port'])

    def get_blockchain_stats(self):
        try:
            response = requests.get(self.blockchain_url + '/get_statistics')
            resp_blockchain = response.json() 
            last_block_header = resp_blockchain['last_block_header']
            unique_wallet_addresses = resp_blockchain["unique_wallet_addresses"] 
            total_coins = resp_blockchain["total_coins"]  
            return last_block_header, unique_wallet_addresses, total_coins
        except Exception as e:
            print(f"Error getting Blockchain stats: {str(e)}")
            return None, None, None

    def get_pool_stats(self):
        try:
            response = requests.get(self.pool_url + '/transactions_statistics')
            transactions_data = response.json()
            num_submitted_transactions = transactions_data["submitted_transactions"]
            num_unconfirmed_transactions = transactions_data["unconfirmed_transactions"]
            return num_submitted_transactions, num_unconfirmed_transactions
        except Exception as e:
            print(f"Error getting Pool stats: {str(e)}")
            return None, None

    def get_metronome_stats(self):
        try:
            response = requests.get(self.metronome_url + '/get_metronome_info')
            metronome_data = response.json()
            num_validators = metronome_data["validators"]
            hashes_per_sec = metronome_data["hashes_per_sec"]
            total_hashes_stored = metronome_data["total_hashes_stored"]
            return num_validators, hashes_per_sec, total_hashes_stored
        except Exception as e:
            print(f"Error getting Metronome stats: {str(e)}")
            return None, None, None


if __name__ == "__main__":

    monitor = Monitor()

    last_block_header, unique_wallets, total_coins = monitor.get_blockchain_stats()
    print(f"Blockchain Stats: Last Block Header: {last_block_header}, Unique Wallets: {unique_wallets}, Total Coins: {total_coins}")

    num_submitted, num_unconfirmed = monitor.get_pool_stats()
    print(f"Pool Stats: Submitted Transactions: {num_submitted}, Unconfirmed Transactions: {num_unconfirmed}")

    validators, hashes_sec, total_hashes = monitor.get_metronome_stats()
    print(f"Metronome Stats: Validators: {validators}, Hashes per Second: {hashes_sec}, Total Hashes Stored: {total_hashes}")
