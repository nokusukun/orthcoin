import sha3
import eth_keys
from eth_keys import KeyAPI
from eth_keys.backends import NativeECCBackend

import pycoin.ecdsa as ecd 
import hashlib, json, datetime


DIGEST = sha3.keccak_256
keyapi = KeyAPI(NativeECCBackend)

# -[ Transaction Validation ]- ################################
#   Note: This set of functions is unused and deprecrated      #
#           Please use abc.Transaction to validate              #
                                                                #
def validate_sender_as_signer(transaction):                     #
    jsonified = transaction                                     #
    pubkey = jsonified['senderPubKey']                          #
    sender = jsonified['from']                                  #
    c_pubkey = ETH_misc.c_pubkey_to_address(ETH_misc.compress_pubkey(pubkey))                                           #
    return sender == c_pubkey     #
                                                                #
def get_transaction_hash(transaction):                          #
    data = {"from": transaction["from"],
            "to": transaction["to"],
            "senderPubKey": transaction["senderPubKey"],
            "value": transaction["value"],
            "fee": transaction["fee"],
            "dateCreated": transaction["dateCreated"]}                                #
    return ETH_misc.sha256(
                json.JSONEncoder(separators=(',', ':')).encode(data)
            )                                                   #
                                                                #
def validate_transaction_data(transaction):                     #
    if transaction['from'] == 'coinbase':                       #
        return True, "201:TransactionIsCoinbase"                #
    pubkey = transaction['senderPubKey']                        #
    if not validate_sender_as_signer(transaction):              #
        return False, "301:SenderSignerMismatch"                #
                                                                #
    hash_trans = get_transaction_hash(transaction)              #
    sig_trans = transaction['senderSignature']                  #
    result = ecd.verify(ecd.generator_secp256k1,                #
                pubkey,                                         #
                int(hash_trans, base=16),                       #
                sig_trans)                                      #
    if result:                                                  #
        return True, "200:TransactionValid"                     #
    else:                                                       #
        return False, "300:TransactionInvalid"                  #


# -[ Block Validation ]- ######################################
                                                               #
def validate_coinbase_transaction(block):
    coinbase = [x for x in block['transactions']
                if x['from'] == 'coinbase']
    if not coinbase:
        return False, "NoCoinbaseInBlock"                

    coinbase = coinbase[0]
    transactions = [x for x in block['transactions']
                    if x['from'] != 'coinbase']

    expected_sum =  sum(t['fee'] for t in transactions) \
                    + 1000

    if coinbase['value'] != expected_sum:
        return False, "CoinbaseRewardMismatch"

    return True, "ValidCoinbaseTransaction"


def validate_block_transactions(block):
    from models.abc import Transaction
    for transaction in block['transactions']:
        if not validate_transaction_data(transaction):
            return False
    return True

def validate_block_hash(block):                                 #
    block = {x: y for x, y in block.items()}                    #
    blockHash = block.pop("blockHash")                          #
    return blockHash == ETH_misc.sha256(json.dumps(block))      #
                                                                #
def validate_nonce(block):                                      #
    block = {x: y for x, y in block.items()}                    #
    data = {                                                    #
            "index": block['index'],                            #
            "transactions": block['transactions'],              #
            "minedBy": block['minedBy'],                          #
            "prevBlockHash": block['prevBlockHash'],            #
            "difficulty": block['difficulty']                   #
            }                                                   #
    blockDataHash = ETH_misc.sha256(json.dumps(data))           #
    return block['blockDataHash'] == blockDataHash              #
                                                                #
def validate_block(block, prevBlockHash):                                      #
    if not validate_block_hash(block):                          #
        return False, "500:BlockHashMismatch"                   #
                                                                #
    if not validate_nonce(block):                               #
        return False, "501:InvalidBlockNonce"                   #

    if not validate_block_transactions(block):
        return False, "501:IllegalTransactions"

    cvalid, cvmessage = validate_coinbase_transaction(block)
    if not cvalid:
        return False, cvmessage

    return True, "400:ValidBlock"

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

