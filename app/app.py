from flask import Flask, jsonify
from datetime import datetime
import os

app = Flask(__name__)

# Versión de la aplicación (puede ser configurada via env var)
APP_VERSION = os.getenv('APP_VERSION', '1.0.0')

@app.route('/')
def home():
    return jsonify(
        message="Hello from Flask on AKS!",
        version=APP_VERSION,
        timestamp=datetime.utcnow().isoformat()
    )

@app.route('/health')
def health():
    return jsonify(
        status="healthy",
        version=APP_VERSION,
        timestamp=datetime.utcnow().isoformat(),
        uptime="running",
        checks={
            "database": "ok",
            "cache": "ok",
            "external_api": "ok"
        }
    ), 200

@app.route('/info')
def info():
    """Endpoint que proporciona información sobre la aplicación"""
    return jsonify(
        application="Flask API",
        version=APP_VERSION,
        environment=os.getenv('ENVIRONMENT', 'development'),
        hostname=os.getenv('HOSTNAME', 'unknown'),
        timestamp=datetime.utcnow().isoformat(),
        endpoints=[
            "/",
            "/health",
            "/info"
        ]
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)