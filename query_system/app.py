from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess

app = Flask(__name__)
CORS(app)  # lets browser comm with this api

@app.route('/ask', methods=['POST'])
def ask_query():
    data = request.get_json()
    user_question = data.get('question', '')

    if not user_question:
        return jsonify({"error": "No question provided"}), 400

    # Run query.py script as a subprocess
    # safely captures output
    try:
        result = subprocess.run(
            ['python3', 'query.py', user_question],
            capture_output=True,
            text=True,
            check=True
        )

        clean_output = result.stdout.strip()

        return jsonify({"answer": clean_output})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting server on http://localhost:5000")
    app.run(debug=True, port=5000)