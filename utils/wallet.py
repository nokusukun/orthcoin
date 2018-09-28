from rainbowsocks.rainbowsocks import RainbowSocksClient
from . import sign

class OrthAccount():

	def __init__(self, private_key, endpoint):
		self.wallet = sign.Key(private_key)
		self.endpoint = RainbowSocksClient(endpoint)
		self.endpoint.connect()

	@property
	def balance(self):
		return self.endpoint.request("address.balance", self.wallet.address)

	def send(self, address, value):
		obj, tx_hash = self.wallet.sign_transaction(**{
				"recipient_address": address, 
				"value": value, 
				"fee": 100})
		obj.update({"origin": {"nodeid": "orth-account-client-app"}})

		if self.balance < value + 100:
			raise Exception("Not enough balance to send transaction.")

		print(f"Submitting Transaction: {obj['from']}@{obj['value']} -> {obj['to']}")
		result = self.endpoint.request("transaction.new", obj)
		if "success" in result:
			return tx_hash
		else:
			return result

	def transactions(self, _range=10):
		transactions = self.endpoint.request("address.transactions", {"range": _range, "address": self.wallet.address})
		return transactions