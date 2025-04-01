from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/')
def home():
    return "API Flask funcionando"

# [Aquí tu lógica actual de scraping]

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
