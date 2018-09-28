import pycoin.ecdsa as ecd 
import hashlib, json
import datetime

class ETH_misc():

    @staticmethod
    def ripemd160(msg):
        return hashlib.new('ripemd160', msg.encode('utf-8')).hexdigest()

    @staticmethod
    def sha256(msg):
        return hashlib.new('sha256', msg.encode('utf-8')).hexdigest()

    @staticmethod
    def key_to_int(key):
        return int(key, base=16)

    @staticmethod
    def generate_pubkey_from_int(key):
        return (ecd.generator_secp256k1 * key).pair()

    @staticmethod
    def compress_pubkey(key):
        return hex(key[0])[2:] + str(key[1] % 2)

    @staticmethod
    def c_pubkey_to_address(c_pubkey):
        return ETH_misc.ripemd160(c_pubkey)

    @staticmethod
    def pubkey_add_generator(privkey):
        pubkey = ETH_misc.generate_pubkey_from_int(privkey)
        c_pubkey = ETH_misc.compress_pubkey(pubkey)
        print("Compressed pubkey:", c_pubkey)
        address = ETH_misc.c_pubkey_to_address(c_pubkey)
        print("Address", address)
        return c_pubkey, address


class Key():
    def __init__(self, key):
        self.privkey = key

    @property
    def int(self):
        return ETH_misc.key_to_int(self.privkey)

    @property
    def pubkey(self):
        return ETH_misc.generate_pubkey_from_int(self.int)

    @property
    def c_pubkey(self):
        return ETH_misc.compress_pubkey(self.pubkey)

    @property
    def address(self):
        return ETH_misc.c_pubkey_to_address(self.c_pubkey)

    def sign_transaction(self, **data):
        to_address = data.pop("recipient_address")
        value = data.pop("value")
        fee = data.pop("fee")

        transaction = {
            "from": self.address,
            "to": to_address,
            "senderPubKey": self.pubkey,
            "value": value,
            "fee": fee,
            "dateCreated": int(datetime.datetime.now().timestamp())
        }

        json_trans = json.JSONEncoder(separators=(',', ':')).encode(transaction)
        hash_trans = ETH_misc.sha256(json_trans)
        sig_trans = ecd.sign(ecd.generator_secp256k1, self.int, int(hash_trans, base=16))
        transaction['senderSignature'] = [hex(sig_trans[0])[2:], hex(sig_trans[1])[2:]]
        #print(f"=====Transaction JSON=====\n{json_trans}")
        #print(f"=====Transaction Hash=====\n{hash_trans}")
        #print(f"=====Transaction Sig=====\n{sig_trans}")
        #print(f"=====Signed Transaction=====\n{json.dumps(transaction, indent=2)}")

        verification = ecd.verify(
            ecd.generator_secp256k1, 
            self.pubkey, 
            int(hash_trans, base=16), 
            sig_trans)
        #print(f"VALIDATION: {verification}")

        transaction['transactionDataHash'] = hash_trans
        transaction['senderSignature'] = sig_trans
        transaction['transferSuccessful'] = False
        transaction['minedInBlockIndex'] = None

        return transaction, json.dumps(transaction)