from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def get_map_context():
    try:
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

@app.route('/api/chat', methods=['POST', 'GET'])
def chat():
    if request.method == 'GET':
        return jsonify({"status": "API calisiyor!"})
    
    if not GROQ_API_KEY:
        return jsonify({"reply": "Sistem Hatası: API KEY eksik!"}), 500

    user_data = request.json
    user_message = user_data.get("message", "")
    # Frontend'den gelen geçmiş mesajları alıyoruz
    history = user_data.get("history", []) 
    
    map_data = get_map_context()

    # BOTUN TAKILMAMASI İÇİN GÜNCELLENEN PROMPT
    system_prompt = f"""Sen Kadıköy'deki Tamir ve Dönüşüm Ağı'nın (Repair Hub) enerjik, samimi ve uzman yapay zeka asistanısın.
Kullanıcıların eşyalarını çöpe atmak yerine onarmalarına destek olarak sürdürülebilirliğe katkı sağlıyorsun.

GÖREVLERİN VE KİMLİĞİN:
1. İLETİŞİM VE İSİM: Geçmiş mesajlardan kullanıcının adını biliyorsan ona her zaman ismiyle hitap et. Adını hiç söylemediyse, ilk mesajında yardımcı olmakla beraber samimi bir dille adını da öğrenmek iste. Asla tekrar tekrar isim sorma.
2. DOĞRUDAN ÇÖZÜM ODAKLI OL: Kullanıcı "merhaba", "telefonum bozuldu" vb. dediğinde hemen konuya gir. Nasıl tamir edileceğine dair ufak ipuçları ver veya doğrudan uygun tamirciyi öner.
3. YEREL BİLGİYİ (VERİLERİ) KULLAN: Sana sağlanan "Veriler" kısmındaki tamirciler listesini zekice kullan. Kullanıcının sorununa uygun olabilecek 2-3 tamirciyi seç ve "Bak, listemizde şöyle yerler var..." diyerek isimlerini öner. 
4. TARZ: Robot gibi değil, mahallenin yardımsever ve pratik tamircisi gibi konuş. Kısa, net ve hevesli ol. Emoji kullanmaktan çekinme!

Kullanıcı arayüzü açtığında zaten "Merhaba bugün neyi tamir ediyoruz! :)" mesajını görüyor. O yüzden doğrudan konuya girebilirsin.

Veriler: {map_data}"""

    # API'a gönderilecek mesaj listesini oluşturuyoruz
    messages = [{"role": "system", "content": system_prompt}]
    
    # Geçmişi ekle (Assistant ve User rollerini eşleştirerek)
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["text"]})
    
    # En son mesajı ekle
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 400
    }

    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                 headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}, 
                                 json=payload)
        data = response.json()
        return jsonify({"reply": data["choices"][0]["message"]["content"]})
    except Exception as e:
        return jsonify({"reply": f"Hata: {str(e)}"}), 500