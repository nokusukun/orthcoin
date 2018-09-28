import atexit
import threading
import json
import datetime
import asyncio
from pprint import pprint

from rainbowsocks.rainbowsocks import RainbowSocksServer, RainbowSocksClient
from models.abc import Node, Transaction, BlockJob
from utils import utils


rainbowserver = RainbowSocksServer()
NODE = Node()

##### NODE ENDPOINTS

def pingAllNodes():
    for nid, peer in list(NODE.connected_nodes.items()):
        try:
            print(f"Pinging {nid}")
            r = peer.request("node.ping", {})
        except: 
            print(f" -> Not responding, removing...")
            NODE.connected_nodes.pop(nid)
            NODE.network_nodes.pop(nid)


def cleanUp():
    for nid, peer in list(NODE.connected_nodes.items()):
        print(f"Sending disconnect to {nid}")
        peer.request("node.disconnect", {}, True)
        peer.connection.close()

def syncToNode(remoteNodeConnection):
    peerChain = remoteNodeConnection.request("block.get.all", {})
    if len(peerChain) > len(NODE.chain):
        print(" -> Ingesting Chain")
        NODE.chain = peerChain
        NODE.pending_transactions = remoteNodeConnection.request("transaction.pending.all", {})

    network = remoteNodeConnection.request("node.getNetwork", {})
    for credentials in network:
        if credentials['nodeid'] != NODE.credentials['nodeid']:
            print(list(NODE.connected_nodes.keys()))
            if credentials['nodeid'] not in NODE.connected_nodes:
                print(f"-> Syncing with {credentials}")
                connectToNode(credentials)


def connectToNode(credentials, state="Main"):
    print(f"[{state}@{credentials['nodeid']}] Attempting to connect: {credentials}")
    print(f"{state}@{credentials['nodeid']} -> {NODE.connected_is_full}")
    if credentials['nodeid'] not in NODE.connected_nodes    \
        and not NODE.connected_is_full                      \
        and credentials['nodeid'] != NODE.credentials['nodeid']:

        print(f"{state}@{credentials['nodeid']} -> Establishing connection to {credentials['nodeid']}...")
        remoteNodeConnection = RainbowSocksClient(credentials['host'])
        print(f"{state}@{credentials['nodeid']} -> Adding to nodes")
        NODE.connected_nodes[credentials['nodeid']] = remoteNodeConnection

        remoteNodeConnection.event("SERVERDISCONNECT")(pingAllNodes)
        remoteNodeConnection.connect()

        print(f"{state}@{credentials['nodeid']} -> Connected")
        if not credentials.get('nrc', False):
            print(f"{state}@{credentials['nodeid']} -> NRC Connection")
            payload = NODE.credentials
            payload.update({"nrc": False})
            response = remoteNodeConnection.request('node.connect', payload, True)
            threading.Thread(target=syncToNode, args=(remoteNodeConnection,)).start()
            
            #if response != "OK":
            #    print(" !! Node didn't reply with 'OK'")
            #    return False


    print(f"{state}@{credentials['nodeid']} -> Established")
    return True


@rainbowserver.event("node.connect")
async def newConnectionFromNode(sock, data):
    """
    node.connect
        Establish Node connection.

        Expected Payload:
            JSON/DICT  -> Node.credentials
                nodeid -> str[32 MAX]: Unique string, used for node identification.
                host   -> Websocket URI: Node server URI
                            "ws://hostname:port"
                nrc -> Bool: No return connect, True if there's no need to check.

        Returns:
            "OK": Connection Successful and your node has been broadcasted.
            "Failed": Node did not 
        
    """
    print(f"node.connect from {data}")
    # Establishes return connection to remote node
    # Connect back if Node still has space for connections
    result = connectToNode(data)
    if result:
        await sock.respond("OK")
    else:
        return await sock.respond("Failed")

    # Broadcast new node to the network.
    if data['nodeid'] not in NODE.network_nodes:
        NODE.network_nodes[data['nodeid']] = data
        for nid, remoteNodeConnection in list(NODE.connected_nodes.items()):
            # Send request but don't wait for a response.
            try:
                remoteNodeConnection.request("node.new.node", data, True)
            except:
                print(f"'{nid}' is not responding, removing...")
                NODE.connected_nodes.pop(nid)

    await sock.respond("OK")


@rainbowserver.event("node.ping")
async def pingNode(sock, data):
    """
    node.ping
        Pings the node

        Expected Payload:
            {} Nothing

        Returns:
            "pong" 
        
    """
    return await sock.respond("pong")


@rainbowserver.event("node.getNetwork")
async def getNetwork(sock, data):
    """
    node.getNetwork
        Get the list of node credentials in the network.

        Expected Payload:
            JSON/DICT -> Node.credentials

        Returns:
            [Node.credentials] -> List of Node.credentials
    """
    return await sock.respond(list(NODE.network_nodes.values()))


@rainbowserver.event("node.disconnect")
async def disconnectNode(sock, data):
    """
    node.disconnet
        Send request of intent to Disconnect on the Node

        Expected Payload:
            Node.credential

        Returns:
            Nothing
        
    """
    NODE.connected_nodes.pop(data['nodeid'])
    NODE.network_nodes.pop(data['nodeid'])


@rainbowserver.event("node.new.node")
async def newNode(sock, data):
    """
    node.new.node
        Recieved everytime a new node connects to the network.

        Expected Payload:
            JSON/DICT -> Node.credentials

        Returns:
            None
    """
    await sock.respond("OK")
    if data['nodeid'] == NODE.nodeid:
        return None
    if data['nodeid'] not in NODE.network_nodes:
        print(f"new node in network: {data}")
        NODE.network_nodes[data['nodeid']] = data
        connectToNode(data)


#### BLOCK ENDPOINTS

@rainbowserver.event("block.get.all")
async def getAllBlocks(sock, data):
    """
    node.ping
        Retrieve the entire chain in the network.

        Expected Payload:
            {} Nothing

        Returns:
            Node.chain: Network Chian
        
    """
    await sock.respond(NODE.chain)

@rainbowserver.event("block.chain.size")
async def getChainSize(sock, data):
    """
    node.ping
        Retrieve the entire chain in the network.

        Expected Payload:
            {} Nothing

        Returns INT:
            Network Chian size
        
    """
    await sock.respond(len(NODE.chain))

@rainbowserver.event("block.get")
async def getBlock(sock, data):
    """
    node.ping
        Pings the node

        Expected Payload:
            {
                index -> INT: block index
            }
            or
            {
                hash -> hex: block hash
            }

        Returns:
            Block -> JSON: Block data
        
    """
    if "index" in data:
        if data['index'] < len(NODE.chain):
            return await sock.respond(NODE.chain[data['index']])
        else:
            return await sock.respond({"error": "Invalid block index."})

    if "hash" in data:
        block = [x for x in NODE.chain if x['blockHash'] == data['hash']]
        if block:
            return await sock.respond(block[0])
        else:
            return await sock.respond({"error": "Block does not exist."})

    return await sock.respond({"error": "'hash' or 'index' not passed."})


@rainbowserver.event("block.integrate")
async def newBlock(sock, data):
    print("New Block in network")
    if data['block']['index'] == len(NODE.chain):
        _v, msg = utils.validate_block(data['block'], NODE.lastBlock['blockHash'])
        #loop = asyncio.get_event_loop()
        #_v, msg = await loop.run_in_executor(None, utils.validate_block, data['block'], NODE.lastBlock['blockHash'])
        if _v:
            integrateBlock(data['block'])

            # Broadcasting
            if 'origin' not in data:
                data['origin'] = [NODE.nodeid]
            else:
                data['origin'].append(NODE.nodeid)

            for nid, remoteNodeConnection in list(NODE.connected_nodes.items()):
                # Send request but don't wait for a response.
                try:
                    if nid not in data['origin']:
                        remoteNodeConnection.request("block.integrate", data, True)
                except:
                    print(f"'{nid}' is not responding, removing...")
                    NODE.connected_nodes.pop(nid)

        else:
            print(f"Illegal block recieved: {msg}\n============ BlockData ==============")
            pprint(data['block'])
            pprint("============ END ==============")
    elif data['block']['index'] < len(NODE.chain):
        print(f"Illegal block index recieved. Expected: {len(NODE.chain)}, Recieved: {data['block']['index']}")
    else:
        print(f"Illegal block index recieved. Expected: {len(NODE.chain)}, Recieved: {data['block']['index']}")
        print("============ BlockData ==============")
        pprint(data['block'])
        print("============ END ==============")



def integrateBlock(block):
    print(f"[BLOCK]: Integrating block: {block['index']}@{block['blockHash'][:8]}...")
    approved_transactions = [x['transactionDataHash'] for x in block['transactions']]
    print(f"{len(approved_transactions)} transactions in Block.")
    NODE.pending_transactions = [x for x in NODE.pending_transactions 
                                if x['transactionDataHash'] not in approved_transactions]
    NODE.chain.append(block)
    NODE.update_balance(block)

    return True


@rainbowserver.event("block.minejob.get")
async def getBlockMineJob(sock, data):
    """
    IN JSON:
        miner STR: Miner address

    OUT JSON:
        datahash STR: block datahash
        blockdata DICT: block data for miner validation
        difficulty INT: block difficulty
    """
    loop = asyncio.get_event_loop()
    pending_transactions = await loop.run_in_executor(None, NODE.validate_transactions, [x for x in NODE.pending_transactions])
    #pending_transactions = NODE.validate_transactions([x for x in NODE.pending_transactions])
    job = BlockJob( data['miner'],
                    NODE.lastBlock['blockHash'],
                    NODE.lastBlock['index'] + 1,
                    NODE.lastBlock['difficulty'],
                    pending_transactions)

    coinbase_transaction = {                                                                                       
                    "from": "coinbase",
                    "to": data['miner'],
                    "senderPubKey": "",
                    "value": sum(t['fee'] for t in pending_transactions) + 1000,
                    "fee": 0,
                    "dateCreated": str(datetime.datetime.now()),
                    "senderSignature": ["",""],
                    "minedInBlockIndex": job.block['index'],
                    "transferSuccessful": True,
                    "transactionDataHash": "00000000000000000000000000000000"                         
                }

    job.block['transactions'].append(coinbase_transaction)
    NODE.pending_blocks[job.datahash] = job                                                                                                             

    await sock.respond({
                    "datahash": job.datahash, 
                    "blockdata": job.fullblock, 
                    "difficulty": job.block['difficulty']
                })

    for nid, remoteNodeConnection in list(NODE.connected_nodes.items()):
        # Send request but don't wait for a response.
        try:
            remoteNodeConnection.request("block.minejob.integrate", job.jobdata, True)
        except:
            print(f"'{nid}' is not responding, removing...")
            NODE.connected_nodes.pop(nid)


@rainbowserver.event("block.minejob.integrate")
async def intergrateBlockJob(sock, data):
    """
    IN JSON:
        "data" DICT: BlockJob.jobdata property
            "block" DICT: BlockJob.block property
            "nonce" INT: BlockJob.nonce property
            "jobCreated" STR:  BlockJob.jobCreated property
    OUT NONE
    """
    job = BlockJob.loadexternal(data)
    if job.datahash not in NODE.pending_blocks:
        NODE.pending_blocks[job.datahash] = job

        # Propogate block job
        for nid, remoteNodeConnection in list(NODE.connected_nodes.items()):
            # Send request but don't wait for a response.
            try:
                remoteNodeConnection.request("block.minejob.integrate", data, True)
            except:
                print(f"'{nid}' is not responding, removing...")
                NODE.connected_nodes.pop(nid)



@rainbowserver.event("block.minejob.submit")
async def submitBlockMineJob(sock, data):
    """
    Submit mined block
    IN JSON:
        "datahash" STR: BlockJob.datahash property
        "nonce" INT: BlockJob.nonce property
    OUT NONE
    """
    datahash = data.get('datahash', None)
    nonce = data.get('nonce', None)
    job = NODE.pending_blocks.get(datahash, None)

    if job.block["index"] != NODE.lastBlock['index'] + 1:
        return await sock.respond({"error": "block has already been mined."})

    if not nonce:
        return await sock.respond({"error": "'nonce' is not specified."})
    if not job:
        return await sock.respond({"error": "'datahash' not in pending blocks."})

    # Note: Refactor validation to be clearer.
    if not job.validate(data):
        return await sock.respond({"error": f"'nonce' doesn't compute to correct difficulty. (Nonce: {nonce})"})

    integrateBlock(job.fullblock)
    await sock.respond({"result": "confirmed"})
    # Propogate block
    for nid, remoteNodeConnection in list(NODE.connected_nodes.items()):
        # Send request but don't wait for a response.`
        try:
            print(f"Propogating Block to {nid}")
            payload = {"origin": [NODE.credentials['nodeid']], "block": job.fullblock}
            remoteNodeConnection.request("block.integrate", payload, True)
        except:
            print(f"'{nid}' is not responding, removing...")
            NODE.connected_nodes.pop(nid)


#### TRANSACTION ENDPOINTS

@rainbowserver.event("transaction.new")
async def newTransaction(sock, data):
    origin = data.pop('origin')
    transaction = Transaction(json.dumps(data))
    
    if data['transactionDataHash'] not in [x['transactionDataHash'] for x in NODE.pending_transactions]:

        if not transaction.valid:
            print("Invalid Transaction, rejecting")
            return await sock.respond({"error": "Invalid transaction"})

        print(f"[NEW_TX]: {data['from'][:6]}...@{data['value']} -> {data['to'][:6]}...")
        print(f"Transaction Validation Result: {transaction.valid}")
        if (transaction.value + transaction.fee) > NODE.get_balance(transaction._from):
            print(f"[ERROR] Rejecting transaction, insufficient funds.")
            return await sock.respond({"error": "Not enough balance."})
        print("New transaction in network.")
        print(f" -> {data['transactionDataHash']}")

        await sock.respond({"success": "Transaction Validated"})
        NODE.pending_transactions.append(data)
        data['origin'] = NODE.credentials
        for nid, remoteNodeConnection in list(NODE.connected_nodes.items()):
            print(f" -> Propogating {nid}")
            if nid != origin['nodeid']:
                try:
                    remoteNodeConnection.request("transaction.new", data, True)
                except:
                    print(f"'{nid}' is not responding, removing...")
                    NODE.connected_nodes.pop(nid)
    else:
        await sock.respond({"error": "Transaction already in network"})


@rainbowserver.event("transaction.pending.all")
async def allPendingTransaction(sock, data):
    await sock.respond(NODE.pending_transactions)


#### ADDRESS ENDPOINTS
@rainbowserver.event("address.balance")
async def addressBalance(sock, data):
    """
    Get balance
    IN STR:
        address STR: address
    OUT INT:
        balance INT: account balance
    """
    await sock.respond(NODE.get_balance(data))


@rainbowserver.event("address.transactions")
async def addressTransactions(sock, data):
    """
    Get balance
    IN STR:
        address STR: address
        range INT Optional: block range, e.g 5 = last 5 mined blocks
    OUT abc.Transaction[]: List of transactions
    """
    def tag_pending(data, ispending):
        data['pending'] = ispending
        return data

    transactions = []
    for block in NODE.chain[(data.get('range', 0) / -1):]:
        transactions.extend(tag_pending(x, False) for x in block["transactions"] if x['from'] == data['address'] or x['to'] == data['address'])

    transactions.extend(tag_pending(x, True) for x in NODE.pending_transactions if x['from'] == data['address'] or x['to'] == data['address'])
    
    #pprint(transactions)
    await sock.respond(transactions)



if __name__ == "__main__":
    import sys, os
    atexit.register(cleanUp)
    print(sys.argv)
    NODE._loadconfig(sys.argv[1])
    if NODE.initialnode:
        threading.Thread(target=connectToNode, args=(NODE.initialnode, "Internal State")).start()
        #connectToNode(NODE.initialnode)
    rainbowserver.run(NODE.host, NODE.port)