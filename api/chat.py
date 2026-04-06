from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os

app = Flask(__name__)
CORS(app)

# Vercel Environment Variables'dan API keyi alıyoruz
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def get_map_context():
    try:
        # Dosya yolunu Vercel'e uygun şekilde mutlak (absolute) yapıyoruz
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, 'kadikoy_map_data.json')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            summarized = {
                "tamir_agi": [f"{i.get('name')}" for i in data.get("tamir_agi_noktalari", [])],
                "tamirciler": [f"{i.get('name')}" for i in data.get("tamirci_listesi", [])]
            }
            return json.dumps(summarized, ensure_ascii=False)
    except Exception as e:
        return f"Veri okunamadı: {str(e)}"

# Rota adını dosya adıyla aynı yapıyoruz (/api/chat)
@app.route('/api/chat', methods=['POST', 'GET'])
def chat():
    # Tarayıcıdan test edebilmek için GET metodu ekledim
    if request.method == 'GET':
        return jsonify({"status": "API calisiyor!"})
    
    if not GROQ_API_KEY:
        return jsonify({"reply": "Sistem Hatası: Vercel ayarlarına GROQ_API_KEY eklenmemiş!"}), 500

    user_data = request.json
    user_message = user_data.get("message", "")
    
    if not user_message: 
        return jsonify({"reply": "Mesaj boş Ilgın!"}), 400

    map_data = get_map_context()
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = f"Sen Kadıköy 'Tamir & Ödül' platformu asistanısın. Kişinin ismini sor hitap etmek için. Veriler: {map_data}. Kısa ve öz ol. Düzgün bir Türkçe kullan."

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 400
    }

    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        data = response.json()
        if response.status_code == 200:
            return jsonify({"reply": data["choices"][0]["message"]["content"]})
        return jsonify({"reply": f"Groq Hatası: {data.get('error', {}).get('message')}"})
    except Exception as e:
        return jsonify({"reply": f"İstek atılamadı: {str(e)}"}), 500