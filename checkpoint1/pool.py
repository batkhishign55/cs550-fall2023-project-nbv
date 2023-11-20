import datetime
from flask import Flask, request
import yaml

app = Flask(__name__)


@app.route('/')
def hello():
    return 'Pool'


# curl -X POST localhost:10001/txn -H 'Content-Type: application/json' -d '{"wallet":"some_address","txn_id":"some_id"}' {"message":"transaction received"}
@app.post('/txn')
def receive_txn():
    print(request.json)
    print(datetime.datetime.now(), "  Transaction id " +
          request.json["txn_id"] + " received from " + request.json["wallet"], " ACK")
    return {"message": "transaction received"}


def load_config():
    with open("dsc-config.yaml", "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


config = load_config()
print(datetime.datetime.now(), " DSC " + config["version"])
print(datetime.datetime.now(), " ", "Pool started with 4 worker threads")
