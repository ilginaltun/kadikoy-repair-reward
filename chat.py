#sonnnn

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

@app.route('/api/chat', methods=['POST', 'GET'])
def chat():
    if request.method == 'GET':
        return jsonify({"status": "API aktif, tum tamirciler yuklendi!"})
    
    if not GROQ_API_KEY:
        return jsonify({"reply": "Hata: GROQ_API_KEY eksik!"}), 500

    user_data = request.json
    user_message = user_data.get("message", "")
    history = user_data.get("history", [])[-2:]

    # TUM LOKASYONLARIN KATEGORİZE EDİLMİŞ HALİ
    system_prompt = """Sen Kadıköy Tamir Ağı asistanısın. Ilgın'a ismiyle hitap et.
    SADECE VE SADECE ŞU LİSTEDEKİ GERÇEK MEKANLARI ÖNEREBİLİRSİN:

    [ELEKTRONİK TAMİR]: Gemici Elektrik, Genç Elektrik, Uğur Elektronik, Akar Elektrik, Karaca Elektrik, Metin Elektrik, Televizyon ve Kart Tamiri Atölyesi, Bilgisayar Mühendisleri Odası Yanı Tamirci.
    
    [MOBİLYA VE AHŞAP]: Mo De Döşeme, SIR Mobilya Marangoz, Moda Marangoz, Emir Mobilya, Evren Mobilya, Kadıköy Antikacılar Çarşısı Mobilya Tamiri, Tasarım Atölyesi Kadıköy (TAK).
    
    [TEKSTİL VE TERZİ]: Roventea Terzi, Terzi Kemal, Terzi Yakup, Rüzgar Terzi, Dry Station, Yağmur Terzi, Hak Pasajı Terzileri, Jet Terzi, Terzi Hulusi, Terzi Bayram, Kadıköy Halk Eğitim Merkezi.
    
    [AYAKKABI, ÇANTA, SAAT]: Moda Lostra, Kundura Tamir, Develi Lostra, Adliye Çarşısı Çanta/Ayakkabı Tamir, Erol Saat, Kadıköy Saat Evi, Noy Saat, Taşçılar Optik İçi Saat Tamiri.
    
    [TESİSAT VE DİĞER]: Durmuşoğlu Otopark (Lastik), Acar Tesisat, Doğan Tesisat, Yılmaz Su Tesisatı, Aykar Yapı Tesisat, Işın Apt. Su Tesisatı, Volkan Özdemir Gitar Atölyesi, Kafkas Pasajı Çalgı Tamiri, Moda Bisiklet.

    [DİKKAT]: Yukarıdaki listede 'Nokta' olarak işaretlenen yerleri 'Kentsel Tamir Durağı' olarak genelleyebilirsin. 

    KESİN KURALLAR:
    1. Bu listede yazmayan "Ayşe, Mehmet, Ali, Enderoğlu, Dürbün Elektronik" gibi isimleri ASLA uydurma.
    2. Telefon numarası veya adres uydurma.
    3. Kullanıcı hangi kategoriyi seçtiyse o listeden 2 tane isim seç ve 'Seni şuraya yönlendirebilirim' de.
    4. Kısa, samimi ve emojili cevap ver."""

    payload = {
        "model": "llama3-70b-8192", 
        "messages": [{"role": "system", "content": system_prompt}] + 
                    [{"role": m["role"], "content": m["text"]} for m in history] + 
                    [{"role": "user", "content": user_message}],
        "temperature": 0.0 # Sıfır yaratıcılık, tam gerçeklik.
    }

    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                 headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}, 
                                 json=payload)
        res_data = response.json()
        return jsonify({"reply": res_data["choices"][0]["message"]["content"]})
    except Exception as e:
        return jsonify({"reply": f"Bağlantı pürüzlü kanka: {str(e)}"}), 500