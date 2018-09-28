import yaml
import json
import os

from rainbowsocks.rainbowsocks import RainbowSocksServer, RainbowSocksClient
import tasho

def verify_transaction(data):
    return True


class Node:

    def __init__(self, config='settings.yaml'):
        self._loadconfig(config)
        self.nodes = []
        self.pending_transactions = {}
        self.connected_socks = {}
        self.blocks = []
        #try:
        #    self.database = tasho.Database.open(self.databaseName)
        #except:
        #    self.database = tasho.Database.new(self.databaseName)
        #self.configdb = self.database.table.configdb
        self.server = None

    def _loadconfig(self, file='settings.yaml'):
        if os.path.exists(file):
            with open(file) as f:
                self.__dict__.update(yaml.load(f.read()))


    def start(self):
        if self.startingNode:
            self.connectnodes([self.startingNode])

        self.server = RainbowSocksServer()
        self.server.event('connect.node')(self.server_connnect_node)
        self.server.event('transaction.add')(self.server_add_trasaction)
        self.server.event('transaction.pending')(self.server_get_pending_transactions)
        self.server.event('block.getall')(self.server_get_blocks)
        self.server.run(self.host, self.port)


    def connectnodes(self, nodes):
        #print(f"Connected Nodes: {self.connected_socks.keys()}")
        for node in nodes:
            if node['name'] not in self.connected_socks and node['name'] != self.nodeName:
                address = f"ws://{node['host']}:{node['port']}"
                print(f"Connecting to '{node}' {address}")
                sock = RainbowSocksClient(address)
                sock.event('node.update')(self.updatenodelist)
                sock.event('node.newnode')(self.new_node_connected)

                try:
                    sock.connect()
                    data = {"name": self.nodeName, "host": self.host, "port": self.port}
                    r = sock.request('connect.node', data)
                    self.connected_socks[node['name']] = sock

                    if r == "OK":
                        print(f"Connected {data}, {node}")
                        blocks = sock.request('block.getall', {})
                        if len(self.blocks) > len(blocks):
                            self.blocks = blocks
                            self.pending_transactions = sock.request('transaction.pending')

                    if len(self.connected_socks) > self.maxConnections:
                        break
                except:
                    print(f"Failed to connect: {address}")

    #@node.event:node.update
    def updatenodelist(self, socks, data):
        print(f"Recieving List")
        print("==========DATA==========")
        print(data)
        print("==========END==========")
        if len(data['nodes']) > len(self.nodes):
            self.nodes = data['nodes']
        if len(self.connected_socks) < self.maxConnections:
            self.connectnodes([x for x in data['nodes'] if x['name'] not in self.connected_socks])

    #@node.event:node.newnode
    def new_node_connected(self, socks, data):
        if data['name'] not in self.connected_socks:
            print(f"{data['name']} Node Connected to network")
            self.nodes.append(data)
            self.connectnodes([data])

    #@node.server.event:connect.node
    async def server_connnect_node(self, socks, data):
        print(f"'{data['name']}@{data['host']}' just connected.")
        if data['name'] not in [x['name'] for x in self.nodes]:
            self.nodes.append(data)

        await socks.respond({"data": "OK"})
        await socks.broadcast(data, 'node.newnode')
        self.connectnodes([x for x in self.nodes if x['name'] not in self.connected_socks])


    #@node.server.event:transaction.add
    async def server_add_trasaction(self, socks, data):
        # Verify transaction data here

        if verify_transaction(data):
            if data['signature'] not in self.pending_transactions:
                self.pending_transactions.update({data['signature']: data})
                print(f"New transaction added {data}")
                for name, sock in self.connected_socks.items():
                    print(f"Sending transaction to: {name}")
                    sock.request('transaction.add', data, True)

            await socks.respond("OK")
        else:
            await socks.respond("Verify Transaction Failed")

    #@node.server.event:transaction.pending
    async def server_get_pending_transactions(self, socks, data):
        await socks.respond(self.pending_transactions)

    #@node.server.event:block.get
    async def server_get_blocks(self, socks, data):
        await socks.respond(self.blocks)

    #@node.servet.event:block.create
    async def server_create_block(self, socks, data):
        pass