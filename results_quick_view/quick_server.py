from flask import Flask, jsonify, send_from_directory

app = Flask(__name__)

@app.route('/')
def serve_html():
    return send_from_directory('.', 'quick_view_report.html')

@app.route('/data')
def serve_json():
    return send_from_directory('../results/', '2025-03-31-errors.json')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8088)
