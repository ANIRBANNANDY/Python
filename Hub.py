import json
import os
from flask import Flask, render_template

# Ensure we can find the config file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')

with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

app = Flask(__name__)

@app.route('/')
def index():
    # Flask automatically looks in the /templates folder for index.html
    return render_template('index.html', config=config)

if __name__ == '__main__':
    # Hub runs on port 8080 (access from local machine)
    print(f"Hub Dashboard running at http://{config['servers'][0]}:8080")
    app.run(host='0.0.0.0', port=config['hub_port'])
