import readline
import subprocess

from wallet import Wallet


app_info = "DSC: DataSys Coin Blockchain v1.0"

wallet = Wallet()


def handle_input(inp):
    if inp == "./dsc help":
        print(app_info+"\nHelp menu, supported commands:\n./dsc help\n./dsc wallet\n./dsc blockchain\n./dsc pool key\n./dsc metronome\n./dsc validator\n./dsc monitor\n")
    elif inp == "./dsc wallet":
        print("this is wallet")
    elif inp == "./dsc blockchain":
        print("this is blockchain")
    elif inp == "./dsc pool key":
        print("this is pool key")
    elif inp == "./dsc pool":
        print("this is pool")
    elif inp == "./dsc metronome":
        subprocess.Popen(['gunicorn', 'metronome:app', '-b', '127.0.0.1:5000'])
    elif inp == "./dsc validator":
        print("this is validator")
        pass
    elif inp == "./dsc monitor":
        print("this is monitor")
    elif inp == "./dsc wallet help":
        wallet.print_help()
    elif inp == "./dsc wallet create":
        wallet.create_wallet()
    elif inp == "./dsc wallet key":
        wallet.print_keys()
    elif inp == "./dsc wallet balance":
        wallet.get_balance()
    elif inp.startswith("./dsc wallet send"):
        inp_arr = inp.split(" ")
        wallet.send_coins(int(inp_arr[3]), inp_arr[4])
    elif inp.startswith("./dsc wallet transaction "):
        inp_arr = inp.split(" ")
        wallet.check_transaction_status(inp_arr[3])
    elif inp == "./dsc wallet transactions":
        wallet.transactions()
    elif inp == "./dsc validator help":
        print(app_info+"\nHelp menu for validator, supported commands:\n./dsc validator help\n./dsc validator pos_check\n./dsc validator\n")
    elif inp == "./dsc validator pos_check":
        print("this is validator pos_check")
    elif inp == "" or inp == None:
        pass
    else:
        print("Unknown command!\nRun ./dsc help to get started")


def start_app():
    print(app_info+"\n./dsc help to get started")
    while True:
        inp = input()
        try:
            handle_input(inp)
        except Exception as e:
            print(e)


if __name__ == '__main__':
    start_app()
