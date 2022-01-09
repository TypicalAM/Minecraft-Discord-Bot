from mcstatus import MinecraftServer

server = MinecraftServer.lookup('127.0.0.1')
#status = server.status()
#print(status.version.name)
#print(status.players.sample)
print('Printing query')
query = server.query()
print(query.players.names)
