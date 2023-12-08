

import random
from time import sleep
import time
from wallet import Wallet


wallet = Wallet()
txns = []
confs = []
start_time = 0

# def init_wallet():
#     wallet.create_wallet()

def check_bc_connection():
    wallet.get_balance()

def run_test():
    for i in range(128):
        x = random.randint(1,800)
        txn_id = wallet.send_coins(x/100, "")
        txns.append(txn_id)
        print(f"[INFO]: sent {i}/128")

def check_status():
    global confs
    while True:
        res = wallet.transactions(",".join(txns))
        confs += res["Confirmed"]
        count_conf = len(confs)
        count_sub = len(res["Submitted"])
        count_unconf = len(res["Unconfirmed"])
        print(f"[INFO]: Confirmed: {count_conf}, Unconfirmed: {count_unconf}, Submitted: {count_sub}")
        for conf in res["Confirmed"]:
            txns.remove(conf["txn_id"])

        if not txns:
            save_res_to_file()
            break
        sleep(1)

def save_res_to_file():
    with open("latency.txt", "w") as text_file:
        res = f"Started: {start_time}\n"
        for conf in confs:
            res += str(conf)+"\n"
        res += f"Ended: {int(time.time())}"
        text_file.write(res)

if __name__ == "__main__":

    print("[INFO]: initializing wallet...")
    start_time = int(time.time())
    # init_wallet()

    print("[INFO]: checking blockchain connection...")
    check_bc_connection()

    print("[INFO]: starting test...")
    run_test()

    print("[INFO]: checking the transaction status...")
    check_status()
    print("[INFO]: test done!")