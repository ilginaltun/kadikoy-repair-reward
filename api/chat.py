from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import json
import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
DB_PATH = os.path.join(BASE_DIR, 'repair_hub.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            user_role TEXT,
            sender TEXT NOT NULL,
            message TEXT NOT NULL,
            context TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


init_db()


def get_map_context():
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, 'kadikoy_map_data.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            tamirciler = {}
            for kategori, dukkanlar in data.get("tamirciler", {}).items():
                tamirciler[kategori] = [d.get("name") for d in dukkanlar]
            return json.dumps(tamirciler, ensure_ascii=False)
    except Exception as e:
        return f"Veri okunamadı: {str(e)}"


def get_user(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user


def create_user(email, password, role):
    password_hash = generate_password_hash(password)
    created_at = datetime.utcnow().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (email, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
        (email, password_hash, role, created_at)
    )
    conn.commit()
    conn.close()


def save_conversation(user_email, user_role, sender, message, context=None):
    inserted_at = datetime.utcnow().isoformat()
    if context is not None and not isinstance(context, str):
        context = json.dumps(context, ensure_ascii=False)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversations (user_email, user_role, sender, message, context, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_email, user_role, sender, message, context, inserted_at)
    )
    conn.commit()
    conn.close()


@app.route('/api/auth', methods=['POST'])
def auth():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role = data.get('role')

    if not email or not password or role not in ['musteri', 'tamirci']:
        return jsonify({'error': 'Geçerli e-posta, şifre ve rol giriniz.'}), 400

    user = get_user(email)
    if user:
        if user['role'] != role:
            return jsonify({'error': 'Bu e-posta başka bir rol için kayıtlı.'}), 400
        if not check_password_hash(user['password_hash'], password):
            return jsonify({'error': 'Şifre yanlış.'}), 401
        return jsonify({'email': email, 'role': role})

    create_user(email, password, role)
    return jsonify({'email': email, 'role': role, 'registered': True})


@app.route('/api/chat', methods=['POST', 'GET'])
def chat():
    if request.method == 'GET':
        return jsonify({"status": "API calisiyor!", "groq_key_set": bool(GROQ_API_KEY)})
    
    user_data = request.json
    user_email = user_data.get("userEmail")
    user_role = user_data.get("userRole")
    if not user_email:
        return jsonify({"reply": "Lütfen önce hesabına giriş yap."}), 400

    user_message = user_data.get("message", "")
    history = user_data.get("history", []) 
    customer_location = user_data.get("customerLocation")

    save_conversation(user_email, user_role, 'user', user_message, {
        'customerLocation': customer_location,
        'history_length': len(history)
    })

    if not GROQ_API_KEY:
        fallback_reply = "⚠️ AI servisi şu anda yapılandırılmadı. Lütfen admin ile iletişime geç. (GROQ_API_KEY eksik)"
        save_conversation(user_email, user_role, 'assistant', fallback_reply, {})
        return jsonify({"reply": fallback_reply}), 200

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
                                 json=payload,
                                 timeout=30)
        
        if response.status_code != 200:
            error_msg = response.text
            print(f"GROQ API Error: {response.status_code} - {error_msg}")
            return jsonify({"reply": f"API Hatası ({response.status_code}): {error_msg[:200]}"}), 500
        
        data = response.json()
        
        if "choices" not in data or not data["choices"]:
            print(f"Invalid GROQ response: {data}")
            return jsonify({"reply": "API yanıt hatası: choices bulunamadı"}), 500
        
        assistant_reply = data["choices"][0]["message"]["content"]
        save_conversation(user_email, user_role, 'assistant', assistant_reply, {'customerLocation': customer_location})
        return jsonify({"reply": assistant_reply})
    except requests.exceptions.Timeout:
        return jsonify({"reply": "API isteği zaman aşımına uğradı. Lütfen tekrar dene."}), 500
    except requests.exceptions.ConnectionError:
        return jsonify({"reply": "Bağlantı kurulamadı. İnternet bağlantınızı kontrol edin."}), 500
    except Exception as e:
        print(f"Chat error: {type(e).__name__}: {str(e)}")
        return jsonify({"reply": f"Hata: {str(e)[:100]}"}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)