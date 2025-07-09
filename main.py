# ----------------------------------------------- #
# Plugin Name           : TradingView-Webhook-Bot #
# Author Name           : fabston                 #
# File Name             : main.py                 #
# ----------------------------------------------- #

from handler import send_alert
import config
import time
from flask import Flask, request, jsonify

app = Flask(__name__)


def get_timestamp():
    timestamp = time.strftime("%Y-%m-%d %X")
    return timestamp


@app.route("/webhook", methods=["POST"])
def webhook():
    print("---- NUEVO POST ----", flush=True)
    print("Headers:", dict(request.headers), flush=True)
    print("Raw data:", request.data, flush=True)
    
    #whitelisted_ips = ['52.89.214.238', '34.212.75.30', '54.218.53.128', '52.32.178.7']
    #client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    #if client_ip not in whitelisted_ips:
        #return jsonify({'message': 'Unauthorized'}), 401

    try:
        data = request.get_json(force=True)    # fuerza parseo a JSON
        if data.get("key") == config.sec_key:  # compara con tu clave
            print(get_timestamp(), "Alert Received & Sent!", flush=True)
            send_alert(data)                   # llama al handler
            return jsonify({"message": "OK"}), 200
        else:
            print("Clave incorrecta", flush=True)
            return jsonify({"message": "Bad key"}), 401

    except Exception as e:
        print("ERROR:", e, flush=True)
        return jsonify({"message": "Error"}), 400

@app.route("/", methods=["GET"])
def index():
    return "Webhook bot UP", 200

if __name__ == "__main__":
    from waitress import serve

    serve(app, host="0.0.0.0", port=8080)
