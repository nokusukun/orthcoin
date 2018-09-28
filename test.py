from rainbowsocks.rainbowsocks import RainbowSocksClient
from models.abc import Transaction
from utils import sign
from utils.utils import ETH_misc
import json
from pprint import pprint
import random

import sys

client = RainbowSocksClient(f"ws://nokusu:{sys.argv[2]}")
client.connect()

class P():
	def __init__(self):
		self.silent = False

	def print(self, data):
		if not self.silent:
			print(data)

printer = P()

# Test Send Transaction
def ST():
	key = sign.Key("1234567890")
	obj, json_hash = key.sign_transaction(**{"recipient_address": "053b3ebd1e15f06dfc7e125eadbd31cfec220895", "value": 10000000, "fee": 100})
	obj.update({"origin": {"nodeid": "client"}})
	printer.print("=============== Transaction ================")
	pprinter.print(obj)
	printer.print("================== END =====================")

	printer.print(client.request("transaction.new", obj))
	printer.print("OK!")

# Failed Transaction
def FST():
	key = sign.Key("1234567890")
	obj, json_hash = key.sign_transaction(**{"recipient_address": "053b3ebd1e15f06dfc7e125eadbd31cfec220895", "value": 10000000, "fee": 100})
	obj.update({"origin": {"nodeid": "client"}})
	obj['to'] = "1234567890"

	printer.print(client.request("transaction.new", obj))
	printer.print("OK!")

#def testGetPendingTransactions():
def GPT():
	x = client.request("transaction.pending.all", {})
	printer.print(x)
	return x

# test transaction validation method
def TTV():
	key = sign.Key("62fbe24314ed52de77e919196ff63348181b582773d6d82c56fe21e3e27ba111")
	obj, j = key.sign_transaction(**{"recipient_address": "053b3ebd1e15f06dfc7e125eadbd31cfec220895", "value": 10000000, "fee": 100})
	trans = Transaction(json.dumps(obj))
	printer.print(trans.jsontrans)
	printer.print(f"Wallet Pub Key: {key.pubkey}")
	printer.print(f"{trans.valid}")

# test transaction validation method
def ITTV():
	from pycoin import ecdsa as ecd
	key = sign.Key("62fbe2")
	obj, j = key.sign_transaction(**{"recipient_address": "053b3ebd1e15f06dfc7e125eadbd31cfec220895", "value": 10000000, "fee": 100})
	tx1 = Transaction(json.dumps(obj))
	tx2 = Transaction(tx1.jsontrans)
	obj['to'] = "1234567890"
	trans = Transaction(json.dumps(obj))

	hashes = [	[trans.hash, "False"],							# Modified Recipient Hash
				[trans._d['transactionDataHash'], "True"],	# Valid Hash
			  	["cfd713049033cffda22f25c399b182691716c2b68346d419d5b1edf62fc63740", "False"],
			  	[tx1.hash, "True"],
			  	[tx2.hash, "True"]]

	for _hash, exp_res in hashes:
		printer.print("======Testing=======")
		printer.print(f"HASH: {_hash}")
		result = ecd.verify(ecd.generator_secp256k1,
	                    key.pubkey,
	                    int(_hash, base=16),
	                    trans.senderSignature)
		printer.print(f"VALID? {result}")
		printer.print(f"Expected result: {exp_res}")

def CheckBalance():
	printer.print(client.request("address.balance", "80ed4f00daeafd799d7999d0d60bffab72e02eb6"))

def getMineBlock():
	miner = sign.Key("aabbccddeeff")
	miner_balance = client.request("address.balance", miner.address)
	printer.print(f"Miner Balance: {miner_balance}")
	job = client.request("block.minejob.get", {"miner": miner.address})
	printer.print(f"Index: {job['blockdata']['index']}, Block hash: {job['datahash']}")
	dataHash = ""
	nonce = -1
	while not dataHash.startswith("0" * job['difficulty']):
		nonce += 1
		dataHash = ETH_misc.sha256(f"{job['datahash']}{nonce}")
		
	printer.print(f"Nonce: ND@{nonce}:{dataHash}")

	finished_job = {"datahash": job['datahash'],
					"nonce": nonce}
	result = client.request("block.minejob.submit", finished_job)
	printer.print(f"Result: {result}")
	miner_balance = client.request("address.balance", miner.address)
	printer.print(f"Miner Balance: {miner_balance}")
	return result

def distributeCoins():
	acc = {
		"Reg": sign.Key("1122334455a"),
		"Riko": sign.Key("1234567890b"),
		"Nanachi": sign.Key("1234567890c"),
		"Ozen": sign.Key("1234567890d"),
		"Lyza": sign.Key("1234567890e"),
		"Prushka": sign.Key("1234567890f")
	}

	faucet = sign.Key("4a4c90c69cb27b07650d05763dcebb612fa414c3dd06284086deed464a0866d9")

	for user, wallet in acc.items():
		obj, tx_hash = faucet.sign_transaction(**{
				"recipient_address": wallet.address, 
				"value": 50000, 
				"fee": 100})
		printer.print(f"Submitting Transaction: Faucet@{obj['value']} -> {user}")
		obj.update({"origin": {"nodeid": "client-app"}})
		printer.print(client.request("transaction.new", obj))

def createAndMineTransaction():
	acc = {
		"Reg": sign.Key("1122334455a"),
		"Riko": sign.Key("1234567890b"),
		"Nanachi": sign.Key("1234567890c"),
		"Ozen": sign.Key("1234567890d"),
		"Lyza": sign.Key("1234567890e"),
		"Prushka": sign.Key("1234567890f")
	}
	
	faucet = sign.Key("4a4c90c69cb27b07650d05763dcebb612fa414c3dd06284086deed464a0866d9")
	usera = None 
	userb = None
	for i in range(10):
		usera = random.choice(list(acc.items()))
		userb = random.choice(list(acc.items()))
		while usera == userb:
			userb = random.choice(list(acc.items()))

		obj, tx_hash = usera[1].sign_transaction(**{
				"recipient_address": userb[1].address, 
				"value": random.randint(5000, 10000), 
				"fee": 100})

		obj.update({"origin": {"nodeid": "client-app"}})
		printer.print(f"Submitting Transaction: {userb[0]}@{obj['value']} -> {usera[0]}")

		printer.print(client.request("transaction.new", obj))


def printBalances():
	acc = {
		"Reg": sign.Key("1122334455a"),
		"Riko": sign.Key("1234567890b"),
		"Nanachi": sign.Key("1234567890c"),
		"Ozen": sign.Key("1234567890d"),
		"Lyza": sign.Key("1234567890e"),
		"Prushka": sign.Key("1234567890f")
	}
	print("==============")
	for user, wallet in acc.items():
		_balance = client.request("address.balance", wallet.address)
		printer.print(f"{user} Balance: {_balance}")


def disconnect():
	client.connection.close()

### current test
if sys.argv[1] == "simutx":
	distributeCoins()
	for i in range(20):
		createAndMineTransaction()
elif sys.argv[1] == "mine":
	while True:
		printer.print("Mining Block")
		getMineBlock()
elif sys.argv[1] == "view":
	while True:
		printBalances()
else:
	distributeCoins()
	while True:
		createAndMineTransaction()
		getMineBlock()
#for i in range(5):
#	getMineBlock()