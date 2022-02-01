from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def main():
    return "MOW is online"

def run():
    app.run(host="0.0.0.0", port=8080)

def startKeepAlive():
    server = Thread(target=run)
    server.start()