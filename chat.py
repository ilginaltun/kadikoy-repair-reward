from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# ARTIK DIŞ DOSYA OKUMUYORUZ. VERİLER %100 BURADA.
TAMIRCILER_VERI_TABANI = {
    "Elektronik": ["Gemici Elektrik", "Genç Elektrik", "Uğur Elektronik", "Akar Elektrik", "Televizyon ve Kart Tamiri", "Karaca Elektrik"],
    "Mobilya": ["Mo De Döşeme", "SIR Mobilya Marangoz", "Moda Marangoz", "Emir Mobilya", "Evren Mobilya", "Kadıköy Antikacılar Çarşısı"],
    "Tekstil": ["Roventea Terzi", "Terzi Kemal", "Terzi Yakup", "Rüzgar Terzi", "Dry Station", "Yağmur Terzi", "Hak Pasajı", "Jet Terzi"],
    "Ayakkabi": ["Moda Lostra", "Kundura Tamir", "Develi Lostra", "Adliye Çarşısı Tamir"]
}

@app.route('/api/chat', methods=['POST'])
def chat():
    user_data = request.json
    user_message = user_data.get("message", "")
    history = user_data.get("history", [])[-4:] # Sadece son mesajları hatırla

    # Kesin emirli system prompt
    system_prompt = f"""Sen Kadıköy Tamir Ağı asistanısın. Ilgın'a ismiyle hitap et.
    SADECE ŞU LİSTEDEKİ YERLERİ ÖNEREBİLİRSİN: {TAMIRCILER_VERI_TABANI}
    
    KURALLAR:
    1. Listede olmayan "Ayşe, Mehmet, Ali" gibi isimleri ASLA uydurma.
    2. Telefon numarası uydurma. 
    3. Kullanıcı "Elektronik" derse listeden sadece elektronikçileri seç.
    """

    payload = {
        "model": "llama3-70b-8192", # Akıllı model
        "messages": [{"role": "system", "content": system_prompt}] + 
                    [{"role": m["role"], "content": m["text"]} for m in history] + 
                    [{"role": "user", "content": user_message}],
        "temperature": 0.0 # Sıfır hayal gücü, sadece gerçekler
    }

    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                 headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}, 
                                 json=payload)
        return jsonify({"reply": response.json()["choices"][0]["message"]["content"]})
    except:
        return jsonify({"reply": "Bağlantı pürüzlü!"}), 500