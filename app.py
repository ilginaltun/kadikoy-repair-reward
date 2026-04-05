from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import json
import os
from dotenv import load_dotenv

# .env dosyasındaki değişkenleri yükle
load_dotenv()

app = Flask(__name__, static_folder='.')
CORS(app)

# API Anahtarını sistem değişkenlerinden güvenli bir şekilde alıyoruz
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def get_map_context():
    try:
        # kadikoy_map_data.json dosyasının aynı klasörde olduğundan emin ol
        with open('kadikoy_map_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            summarized = {
                "tamir_agi": [f"{i.get('name')}" for i in data.get("tamir_agi_noktalari", [])],
                "tamirciler": [f"{i.get('name')}" for i in data.get("tamirci_listesi", [])],
                "atik_duraklari": [f"{i.get('name')}" for i in data.get("atik", [])]
            }
            return json.dumps(summarized, ensure_ascii=False)
    except:
        return "Veri yok."

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def send_static(path):
    return send_from_directory('.', path)

@app.route('/chat', methods=['POST'])
def chat():
    user_data = request.json
    user_message = user_data.get("message", "")
    if not user_message: return jsonify({"reply": "Mesaj boş Ilgın!"}), 400

    map_data = get_map_context()
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = f"Sen Kadıköy 'Tamir & Ödül' platformu asistanısın. Ilgın'a ismiyle hitap et. Veriler: {map_data}. Tamir için tamircileri, atölye için ağ noktalarını öner. Kısa ve öz ol."

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 400
    }

    try:
        response = requests.post("https://api.api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        data = response.json()
        if response.status_code == 200:
            return jsonify({"reply": data["choices"][0]["message"]["content"]})
        return jsonify({"reply": f"Hata: {data.get('error', {}).get('message')}"})
    except Exception as e:
        return jsonify({"reply": f"Bağlantı koptu: {str(e)}"}), 500

if __name__ == '__main__':
    # Canlı ortam port ayarı
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port, debug=False)