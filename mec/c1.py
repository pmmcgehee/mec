import socket

clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientsocket.connect(('134.79.116.26', 8089))
clientsocket.send('hello')

