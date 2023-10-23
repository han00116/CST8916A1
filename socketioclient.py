from socketIO_client import SocketIO

def on_stock_price_update(data):
    print('recieved update stock price')

socketIO = SocketIO('http://127.0.0.1', 5000)

socketIO.on('connect', lambda: print('Connected to Websocket'))
socketIO.on('disconnect', lambda: print('disconnected from websocket'))
socketIO.on('stock_price_update', on_stock_price_update)


socketIO.emit('updateStockPrice', {'id':1, 'newPrice': 10.0})

socketIO.wait()