import readline


app_info = "DSC: DataSys Coin Blockchain v1.0"


def startApp():
    print(app_info+"\n./dsc help to get started")
    while True:
        inp = input()
        if inp == "./dsc help":
            print(app_info+"\nHelp menu, supported commands:\n./dsc help\n./dsc wallet\n./dsc blockchain\n./dsc pool key\n./dsc metronome\n./dsc validator\n./dsc monitor\n")
        elif inp == "./dsc wallet":
            print("this is wallet")
            pass
        elif inp == "./dsc blockchain":
            print("this is blockchain")
            pass
        elif inp == "./dsc pool key":
            print("this is pool key")
            pass
        elif inp == "./dsc metronome":
            print("this is metronome")
            pass
        elif inp == "./dsc validator":
            print("this is validator")
            pass
        elif inp == "./dsc monitor":
            print("this is monitor")
            pass
        elif inp == "./dsc wallet help":
            print(app_info+"\nHelp menu for Wallet, supported commands:\n./dsc wallet help\n./dsc wallet create\n./dsc wallet key\n./dsc wallet balance\n./dsc wallet send <amount> <address>\n./dsc wallet transaction <ID>\n")
            pass
        elif inp == "./dsc wallet create":
            print("this is wallet create")
            pass
        elif inp == "./dsc wallet key":
            print("this is wallet key")
            pass
        elif inp == "./dsc wallet balance":
            print("this is wallet balance")
            pass
        elif inp == "./dsc wallet send <amount> <address>":
            print("this is wallet send <amount> <address>")
            pass
        elif inp == "./dsc validator help":
            print(app_info+"\nHelp menu for validator, supported commands:\n./dsc validator help\n./dsc validator pos_check\n./dsc validator\n")
            pass
        elif inp == "./dsc validator pos_check":
            print("this is validator pos_check")
            pass
        else:
            print("Unknown command!\nRun ./dsc help to get help:")


if __name__ == '__main__':
    startApp()
