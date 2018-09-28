from flask import Flask, render_template, abort, url_for, request, flash, session, redirect, send_from_directory, jsonify

from includes.utils import sign
from includes.rainbowsocks.rainbowsocks import RainbowSocksClient
from includes import tasho

import datetime

app = Flask('faucet-app', static_url_path='')
faucet_wallet = sign.Key("4a4c90c69cb27b07650d05763dcebb612fa414c3dd06284086deed464a0866d9")



@app.route("/")
def index():
    return send_from_directory("templates","index.html")

@app.route("/request/<node>/<address>")
def request_wallet(node, address):
    faucet = sign.Key("4a4c90c69cb27b07650d05763dcebb612fa414c3dd06284086deed464a0866d9")
    obj, tx_hash = faucet.sign_transaction(**{
				"recipient_address": address, 
				"value": 1000, 
				"fee": 100})
    obj.update({"origin": {"nodeid": "faucet-app"}})
    client = RainbowSocksClient(node)
    client.connect()
    client.request("transaction.new", obj)
    return jsonify({"result": "OK"})


app.run(host="0.0.0.0", port=80)