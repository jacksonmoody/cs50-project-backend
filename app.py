from flask import Flask, jsonify, request, send_file

app = Flask(__name__)

@app.route("/")
def api():
    return jsonify({
        "message": "Hello World",
        })