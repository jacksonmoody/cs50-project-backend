from flask import Flask

app = Flask(__name__)

@app.route('/', method = ['GET'])

def api():
    return jsonify({"message": "Hello World"})