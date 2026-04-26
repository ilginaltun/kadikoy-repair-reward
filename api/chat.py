from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import json
import os
import csv
import io
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_map_context():
    try:
        file_path = os.path.join(BASE_DIR, 'kadikoy_map_data.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            tamirciler = {}
            for kategori, dukkanlar in data.get("tamirciler", {}).items():
                tamirciler[kategori] = [d.get("name") for d in dukkanlar]
            return json.dumps(tamirciler, ensure_ascii=False)
    except Exception as e:
        return f"Veri okunamadı: {str(e)}"


def get_user(email):
    result = supabase.table('users').select('*').eq('email', email).execute()
    return result.data[0] if result.data else None


def create_user(email, password, role):
    password_hash = generate_password_hash(password)
    supabase.table('users').insert({
        'email': email,
        'password_hash': password_hash,
        'role': role,
        'created_at': datetime.utcnow().isoformat()
    }).execute()


def save_conversation(user_email, user_role, sender, message, context=None):
    if context is not None and not isinstance(context, str):
        context = json.dumps(context, ensure_ascii=False)
    supabase.table('conversations').insert({
        'user_email': user_email,
        'user_role': user_role,
        'sender': sender,
        'message': message,
        'context': context,
        'created_at': datetime.utcnow().isoformat()
    }).execute()


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
        fallback_reply = "⚠️ AI servisi yapılandırılmadı. GROQ_API_KEY eksik."
        save_conversation(user_email, user_role, 'assistant', fallback_reply, {})
        return jsonify({"reply": fallback_reply}), 200

    map_data = get_map_context()

    if user_role == 'tamirci':
        system_prompt = """Sen Kadıköy Repair Hub'ın usta asistanısın. Tamircinin (ustanın) iş bulmasına, işlerini yönetmesine yardımcı oluyorsun. MÜŞTERİYE TAMİRCİ ÖNERMEK senin görevin DEĞİL.

GÖREVLERİN:
1. YAKINDAKI İŞLERİ LİSTELE: Usta "iş var mı", "yakında ne var", "iş bul" gibi bir şey sorduğunda aşağıdaki aktif işleri listele ve aciliyete göre sırala.
2. KATEGORİ BAZLI FİLTRE: "Elektronik iş var mı?", "tekstil geldi mi?" gibi sorularda sadece o kategorideki işleri göster.
3. ACİLİYET VE KAZANÇ: Yüksek aciliyetli ve yüksek puanlı işleri öne çıkar.
4. TARZ: Kısa ve net. Usta ile konuşuyorsun, müşteri değil. "Abi", "kanka" gibi hitaplar uygundur.

AKTİF İŞLER LİSTESİ (bu listeyi kullan, başka kaynak arama):
- 🔴 YÜKSEK ACİL | Kırık Ekran | Elektronik | Müşteri: Ahmet Y. | Konum: Moda Sahil (300m) | 500 Puan
- 🟡 ORTA ACİL | Fermuar Değişimi | Tekstil | Müşteri: Zeynep K. | Konum: Yeldeğirmeni (1.2km) | 150 Puan
- 🟢 DÜŞÜK ACİL | Vites Ayarı | Bisiklet | Müşteri: Can B. | Konum: Osmanağa (800m) | 200 Puan

ÖNEMLI: Tamirciye hiçbir zaman müşteri tarafındaki tamirci dükkanlarını önerme. Sadece yukarıdaki iş listesini kullan."""
    else:
        system_prompt = f"""Sen Kadıköy'deki Tamir ve Dönüşüm Ağı'nın (Repair Hub) enerjik, samimi ve uzman yapay zeka asistanısın.
Kullanıcıların eşyalarını çöpe atmak yerine onarmalarına destek olarak sürdürülebilirliğe katkı sağlıyorsun.

GÖREVLERİN VE KİMLİĞİN:
1. İLETİŞİM VE İSİM: Geçmiş mesajlardan kullanıcının adını biliyorsan ona her zaman ismiyle hitap et. Adını hiç söylemediyse, ilk mesajında yardımcı olmakla beraber samimi bir dille adını da öğrenmek iste. Asla tekrar tekrar isim sorma.
2. DOĞRUDAN ÇÖZÜM ODAKLI OL: Kullanıcı "merhaba", "telefonum bozuldu" vb. dediğinde hemen konuya gir. Nasıl tamir edileceğine dair ufak ipuçları ver veya doğrudan uygun tamirciyi öner.
3. YEREL BİLGİYİ (VERİLERİ) KULLAN: Sana sağlanan "Veriler" kısmındaki tamirciler listesini zekice kullan. Kullanıcının sorununa uygun olabilecek 2-3 tamirciyi seç ve "Bak, listemizde şöyle yerler var..." diyerek isimlerini öner.
4. TARZ: Robot gibi değil, mahallenin yardımsever ve pratik tamircisi gibi konuş. Kısa, net ve hevesli ol. Emoji kullanmaktan çekinme!

Kullanıcı arayüzü açtığında zaten "Merhaba bugün neyi tamir ediyoruz! :)" mesajını görüyor. O yüzden doğrudan konuya girebilirsin.

Veriler: {map_data}"""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["text"]})
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 400
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        if response.status_code != 200:
            return jsonify({"reply": f"API Hatası ({response.status_code}): {response.text[:200]}"}), 500
        data = response.json()
        if "choices" not in data or not data["choices"]:
            return jsonify({"reply": "API yanıt hatası: choices bulunamadı"}), 500
        assistant_reply = data["choices"][0]["message"]["content"]
        save_conversation(user_email, user_role, 'assistant', assistant_reply, {'customerLocation': customer_location})
        return jsonify({"reply": assistant_reply})
    except requests.exceptions.Timeout:
        return jsonify({"reply": "API isteği zaman aşımına uğradı."}), 500
    except requests.exceptions.ConnectionError:
        return jsonify({"reply": "Bağlantı kurulamadı."}), 500
    except Exception as e:
        return jsonify({"reply": f"Hata: {str(e)[:100]}"}), 500


@app.route('/api/export/users', methods=['GET'])
def export_users():
    result = supabase.table('users').select('email, role, created_at').order('created_at', desc=True).execute()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(['Email', 'Rol', 'Kayıt Tarihi'])
    for r in result.data:
        w.writerow([r['email'], r['role'], r['created_at']])
    return Response(out.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=kullanicilar.csv'})


@app.route('/api/export/conversations', methods=['GET'])
def export_conversations():
    result = supabase.table('conversations').select(
        'user_email, user_role, sender, message, created_at'
    ).order('created_at', desc=True).execute()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(['Email', 'Rol', 'Gönderen', 'Mesaj', 'Tarih'])
    for r in result.data:
        w.writerow([r['user_email'], r['user_role'], r['sender'], r['message'], r['created_at']])
    return Response(out.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=konusmalar.csv'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
