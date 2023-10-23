from flask import Flask, request, jsonify
from ariadne import QueryType, MutationType, make_executable_schema, load_schema_from_path
from graphql_server.flask import GraphQLView
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)
stocks = []

type_defs = load_schema_from_path("schema.graphql")

query = QueryType()
mutation = MutationType()

@query.field("stock")
def resolve_stock(_, info, id):
    stock_id = int(id)
    for stock in stocks:
        if stock["id"] == stock_id:
            if "pastPrices" not in stock:
                stock["pastPrices"] = []
            max_price = max(stock["pastPrices"] + [stock["currentPrice"]])
            min_price = min(stock["pastPrices"] + [stock["currentPrice"]])
            stock_with_prices = dict(stock)
            stock_with_prices["maxPrice"] = max_price
            stock_with_prices["minPrice"] = min_price
            return stock_with_prices
    return ValueError("stock not found")
    
@mutation.field("addStock")
def resolve_add_stock(_, info, input):
    name = input.get("name")
    ticker_symbol = input.get("tickerSymbol")
    current_price = input.get("currentPrice")
    if not name or not ticker_symbol or current_price is None:
        raise ValueError("inputs not all correct")
    new_stock = {
        "id": len(stocks) + 1,
        "name": name,
        "tickerSymbol": ticker_symbol,
        "currentPrice": current_price,
        "pastPrices": []
    }
    stocks.append(new_stock)

    socketio.emit('stock added', new_stock, namespace='/stock_updates')

    return new_stock

@mutation.field("updateStock")
def resolve_update_stock(_, info, id, newPrice):
    stock_id = int(id)
    new_price = float(newPrice)

    for stock in stocks:
        if stock["id"] == stock_id:
            past_prices = stock.get("pastPrices", [])
            past_prices.append(stock["currentPrice"])
            stock["pastPrices"] = past_prices
            stock["currentPrice"] = new_price

            socketio.emit('stock_price_update', {"id": stock_id, "newPrice": new_price}, namespace='/stock_updates')

            return stock
    raise ValueError("stock not found")

schema = make_executable_schema(type_defs, query, mutation)


app.add_url_rule("/graphql",view_func=GraphQLView.as_view("graphql", schema = schema, graphiql = True))


@app.route('/api/add_stock', methods = ['POST'])
def add_stock():
    data = request.get_json()
    if not data:
        return jsonify("data provided wrong")
    
    new_id = len(stocks) + 1

    new_stock = {
        'id': new_id,
        "name": data.get("name", ""),
        "tickerSymbol": data.get("tickerSymbol", ""),
        "currentPrice": data.get("currentPrice", 0.0),
        "pastPrices": []
    }

    stocks.append(new_stock)
    return jsonify('stock added successfully'), 201

@app.route('/api/stocks', methods = ['GET'])
def get_all_stocks():
    return jsonify(stocks)

@app.route('/api/update_price/<int:id>', methods = ['PUT'])
def update_stock_price(id):
    data = request.get_json()
    if not data:
        return jsonify("wrong data given"), 400
    
    for stock in stocks:
        if stock["id"] == id:
            current_price = data.get("currentPrice")
            if current_price is not None:
                stock["pastPrices"].append(stock["currentPrice"])
                stock["currentPrice"] = current_price
                return jsonify("price updated successfully")
    return jsonify("stock not found"), 404


@socketio.on('connect')
def handle_connect():
    print('client connected')

@socketio.on('disconnect',namespace='/stock_updates')
def handle_disconnect():
    print('client disconnected')


if __name__ == '__main__':
    socketio.run(host="0.0.0.0", port = 5000)