import os, yaml, json
from collections import defaultdict

import datetime
 
import pycoin.ecdsa as ecd 
from utils import genesisblock
from utils import utils
from utils.utils import ETH_misc

class Node():

    def __init__(self, **kwargs):
        self.connected_nodes = kwargs.get("connected_nodes", {})
        self.network_nodes = kwargs.get("network_nodes", {})

        self.pending_transactions = kwargs.get("pending_transactions", [])
        self.chain = kwargs.get("chain", [genesisblock.genesisblock()])
        self.pending_blocks = kwargs.get("pending_blocks", {})

        # Node configuration
        self.nodeid = kwargs.get("NODEID", "000000000000000000000000000000000")
        self.max_connected_nodes = kwargs.get("MAX_CONNECTED_NODES", 20)
        self.MAX_TRANSACTION_PBLOCK = kwargs.get("MAX_TRANSACTION_PBLOCK", 100)
        self.host = kwargs.get("HOST", "localhost")
        self.port = kwargs.get("PORT", 1120)
        self.initialnode = None
        self.account_balance = {}

    @property
    def lastBlock(self):
        return self.chain[-1]

    @property
    def serverhost(self):
        return f"ws://{self.host}:{self.port}"

    @property
    def credentials(self):
        return {"nodeid": self.nodeid, "host": self.serverhost}

    @property
    def connected_is_full(self):
        return len(self.connected_nodes) >= self.max_connected_nodes

    def _loadconfig(self, file):
        print(f"Attempting to load {file}")
        if os.path.exists(file):
            with open(file) as f:
                self.__dict__.update(yaml.load(f.read()))
                print("  -> OK")

    def _traverse_chain(self):
        self.account_balance = {}
        for block in self.chain:
            self.update_balance(block)

    def update_balance(self, block):
        for tx in block['transactions']:
            if tx['transferSuccessful']:
                if tx['to'] not in self.account_balance:
                    self.account_balance[tx['to']] = 0
                if tx['from'] not in self.account_balance:
                    self.account_balance[tx['from']] = 0
                print(f"[  TX  ]: {tx['from'][:6]}...@{tx['value']} -> {tx['to'][:6]}...")
                val = tx['value']
                self.account_balance[tx['to']] += val
                self.account_balance[tx['from']] -= val + tx['fee']

    def get_balance(self, address):
        if address not in self.account_balance:
            self._traverse_chain()

        bal = self.account_balance.get(address, 0)
        if bal == 0:
            self.account_balance[address] = 0

        return bal

    def validate_transactions(self, transactions):
        _balance = {x: y for x, y in self.account_balance.items()}
        for index, tx in enumerate(transactions):
            print(f"[ CHECK ]: {tx['from'][:6]}...@{tx['value']} -> {tx['to'][:6]}...")
            sender = tx['from']
            reciever = tx['to']
            data_valid, message = utils.validate_transaction_data(tx)
            if not data_valid:
                print("Transaction is invalid:", message)
                transactions[index]['transferSuccessful'] = False

            if sender not in _balance:
               _balance[sender] = self.get_balance(sender)
            if reciever not in _balance:
                _balance[reciever] = self.get_balance(reciever)

            if _balance[sender] < (tx['value'] + tx['fee']) and sender != 'coinbase':
                print(f"Transaction is invalid: {sender} not enough balance.")
                transactions[index]['transferSuccessful'] = False
            else:
                transactions[index]['transferSuccessful'] = True
                _balance[sender] -= tx['value'] + tx['fee']
                _balance[reciever] += tx['value']

        return transactions 



class BlockJob():
    def __init__(self,  miner=None, 
                        lastBlockHash=None, 
                        blockindex=None,
                        difficulty=None,
                        pending_transactions=[]):
        modified_transactions = []
        for transactions in pending_transactions:
            transactions['minedInBlockIndex'] = blockindex

        self.block = {
            "index": blockindex,
            "transactions": pending_transactions,
            "minedBy": miner,
            "prevBlockHash": lastBlockHash,
            "difficulty": difficulty
            }

        self.nonce = None
        self.jobCreated = str(datetime.datetime.now())

    @classmethod
    def loadexternal(BlockJob, data):
        _b = BlockJob()
        _b.__dict__.update(data)
        return _b

    @property
    def jobdata(self):
        data = {"block": self.block,
                "nonce": self.nonce,
                "jobCreated": self.jobCreated}
        return data

    @property
    def fullblock(self):
        block = {}
        block.update(self.block)
        block['blockDataHash'] = utils.ETH_misc.sha256(json.dumps(block))
        block['nonce'] = self.nonce
        block['dateCreated'] = self.jobCreated
        block['blockHash'] = utils.ETH_misc.sha256(json.dumps(block))
        return block

    @property
    def datahash(self):
        return utils.ETH_misc.sha256(json.dumps(self.block))

    def validate(self, job):
        x = f"{self.datahash}{job['nonce']}"
        if utils.ETH_misc.sha256(x).startswith("0" * int(self.block['difficulty'])):
            self.nonce = job['nonce']
            print(f"JobValid: ND@{job['nonce']}:{self.datahash}")
            return True
        else:
            return False


class SuperTransaction():
    pass

class Transaction():
    def __init__(self, data):
        self.raw_data = data
        self._d = json.loads(data)

        self._from = self._d['from']
        self.to = self._d['to']
        self.senderPubKey = self._d['senderPubKey']
        self.value = self._d['value']
        self.fee = self._d['fee']
        self.dateCreated = self._d['dateCreated']

        self.transactionDataHash = self._d['transactionDataHash']
        self.senderSignature = self._d['senderSignature']
        self.minedInBlockIndex = self._d.get("minedInBlockIndex",  None)
        self.transferSuccessful = self._d.get("transferSuccessful",  False)

    @property
    def jsonpartialtrans(self):
        data = {"from": self._from,
                "to": self.to,
                "senderPubKey": self.senderPubKey,
                "value": self.value,
                "fee": self.fee,
                "dateCreated": self.dateCreated}
        
        return json.JSONEncoder(separators=(',', ':')).encode(data)


    @property
    def jsontrans(self):
        data= { 'dateCreated': self.dateCreated,
                'fee': self.fee,
                'from': self._from,
                'minedInBlockIndex': self.minedInBlockIndex,
                'senderPubKey': self.senderPubKey,
                'senderSignature': self.senderSignature,
                'to': self.to,
                'transactionDataHash': self.hash,
                'transferSuccessful': self.transferSuccessful,
                'value': self.value}

        return json.JSONEncoder(separators=(',', ':')).encode(data)

    @property
    def hash(self):
        return ETH_misc.sha256(self.jsonpartialtrans)

    @property
    def valid(self):
        if self.transactionDataHash != self.hash:
            return False
        
       # possible_keypairs = ecd.possible_public_pairs_for_signature(
       #             ecd.generator_secp256k1, 
       #             int(self.hash, 16), 
       #             self.senderSignature)

        #for keypair in possible_keypairs:
        #    print(keypair)
        #    verified = ecd.verify(
        #            ecd.generator_secp256k1,
        #            keypair,
        #            int(self.hash, base=16),
        #            self.senderSignature)
        #    if verified:
        #        return True
        verified = ecd.verify(
                    ecd.generator_secp256k1,
                    self.senderPubKey,
                    int(self.hash, base=16),
                    self.senderSignature)
        
        return verified



class Block():
    def __init__(self, **kwargs):
        self.index = kwargs.get("index", 0)
        self.previous_hash = kwargs.get("previous_hash", "")
        self.timestamp = datetime.datetime.now().timestamp()
        self.transactions = transactions
        self.proof = proof

        if "load_dict" in kwargs:
            self.load(kwargs["load_dict"])

    def load(self, dict):
        self.__dict__.update(dict)

    @property
    def dict(self):
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "proof": self.proof
        }

    @property
    def json(self):
        return json.dumps(self.dict, sort_keys=True)

    @property
    def hash(self):
        return hashlib.sha256(self.json.encode()).hexdigest()


