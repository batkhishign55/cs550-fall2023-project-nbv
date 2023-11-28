import requests
import json

from blockchain import lastblock
from pool import transaction_status

num_submitted_transactions =0
num_unconfirmed_transactions =0

class Monitor:
    def __init__(self):
        pass

    def get_blockchain_stats(self):
        try:
            resp_blockchain = lastblock()
            last_block_header = resp_blockchain['block']
            unique_wallet_addresses = 100  # Need to Replace with actual implementation to count unique wallet addresses
            total_coins = 10000  # Need to Replace with actual implementation to calculate total coins in circulation
            return last_block_header, unique_wallet_addresses, total_coins
        except Exception as e:
            print(f"Error getting Blockchain stats: {str(e)}")
            return None, None, None

    def get_pool_stats(self):
        try:
            transactions_data = transaction_status()
            if transactions_data =='Submitted':
                num_submitted_transactions = num_submitted_transactions + 1
            elif transactions_data =='Unconfirmed':
                num_unconfirmed_transactions = num_unconfirmed_transactions + 1
            return num_submitted_transactions, num_unconfirmed_transactions
        except Exception as e:
            print(f"Error getting Pool stats: {str(e)}")
            return None, None

    def get_metronome_stats(self):
        try:
            response = {"validators":10, "hashes_per_sec": 300, "total_hashes_stored":30}
            metronome_data = response
            num_validators = metronome_data.get('validators', 0)
            hashes_per_sec = metronome_data.get('hashes_per_sec', 0)
            total_hashes_stored = metronome_data.get('total_hashes_stored', 0)
            return num_validators, hashes_per_sec, total_hashes_stored
        except Exception as e:
            print(f"Error getting Metronome stats: {str(e)}")
            return None, None, None

Monitor().get_blockchain_stats()
if __name__ == "__main__":
    

    monitor = Monitor()

    last_block_header, unique_wallets, total_coins = monitor.get_blockchain_stats()
    print(f"Blockchain Stats: Last Block Header: {last_block_header}, Unique Wallets: {unique_wallets}, Total Coins: {total_coins}")

    num_submitted, num_unconfirmed = monitor.get_pool_stats()
    print(f"Pool Stats: Submitted Transactions: {num_submitted}, Unconfirmed Transactions: {num_unconfirmed}")

    validators, hashes_sec, total_hashes = monitor.get_metronome_stats()
    print(f"Metronome Stats: Validators: {validators}, Hashes per Second: {hashes_sec}, Total Hashes Stored: {total_hashes}")
