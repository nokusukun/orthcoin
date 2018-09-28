import datetime
import json

from utils import utils

# private key for faucet account: 4a4c90c69cb27b07650d05763dcebb612fa414c3dd06284086deed464a0866d9
# private key for genesis block: 12345

def genesisblock():
    genesis_transaction = {                                                                                       
                            "from": "053b3ebd1e15f06dfc7e125eadbd31cfec220895",
                            "to": "80ed4f00daeafd799d7999d0d60bffab72e02eb6",
                            "senderPubKey": "e963ffdfe34e63b68aeb42a5826e08af087660e0dac1c3e79f7625ca4e6ae4820",
                            "value": 1000000000000,
                            "fee": 0,
                            "dateCreated": None,
                            "senderSignature": [
                              "d7768896cad27ee23eadb6b7b0f40846480f386e3173d289ba0b3482c0492347",
                              "1f7b8f5e3be31198f28af37a49481eff6202bbf1c1cd3eeae6dbaff37f25f8c0"
                            ],
                            "transactionDataHash": "a5f2a468176b41b3ec42d39a3608706da4b333eb057dd73dae6b16ce16fd5ea1",
                            "minedInBlockIndex": 0,
                            "transferSuccessful": True
                        }

    genesis_transaction['dateCreated'] = str(datetime.datetime.now())

    genesis_block = {
        "index": 0,
        "transactions":[],
        "minedBy": "0000000000000000000000000000000000000000",
        "prevBlockHash": "0000000000000000000000000000000000000000",
        "difficulty": 4
    }

    genesis_block['transactions'] = [genesis_transaction]
    genesis_block['blockDataHash'] = utils.ETH_misc.sha256(json.dumps(genesis_block))

    genesis_block['nonce'] = 0
    genesis_block['dateCreated'] = str(datetime.datetime.now())
    genesis_block['blockHash'] = utils.ETH_misc.sha256(json.dumps(genesis_block))
    return genesis_block

