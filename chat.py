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
        return jsonify({"status": "API zehir gibi calisiyor!"})
    
    if not GROQ_API_KEY:
        return jsonify({"reply": "Sistem Hatası: API KEY eksik!"}), 500

    user_data = request.json
    user_message = user_data.get("message", "")
    # Botun kafası karışmasın diye sadece son 4 mesajı hatırlamasını sağlıyoruz
    history = user_data.get("history", [])[-4:] 
    
    # BÜYÜK MODEL İÇİN SIFIR HALÜSİNASYON PROMPTU
    system_prompt = """Sen Kadıköy Kentsel Tamir Ağı asistanısın. Karşındaki kişinin adı Ilgın.
        
    ELİMİZDEKİ TEK GERÇEK TAMİRCİ LİSTESİ ŞUDUR (BAŞKA HİÇBİR YER YOKTUR):
    [ELEKTRONİK VE TELEFON]: Gemici Elektrik, Genç Elektrik, Uğur Elektronik, Akar Elektrik, Televizyon ve Kart Tamiri Atölyesi, Karaca Elektrik, Elektrikçi
    [MOBİLYA VE AHŞAP]: Mo De Döşeme, SIR Mobilya, Moda Marangoz, Emir Mobilya, Evren Mobilya, Kadıköy Antikacılar Çarşısı
    [TEKSTİL VE TERZİ]: Roventea Terzi, Terzi Kemal, Terzi Yakup, Rüzgar Terzi, Dry Station, Yağmur Terzi, Hak Pasajı Terzileri, Jet Terzi, Terzi Hulusi, Terzi Bayram
    [AYAKKABI VE ÇANTA]: Moda Lostra, Kundura Tamir, Develi Lostra, Adliye Çarşısı Çanta/Ayakkabı Tamir
    [DİĞER]: Durmuşoğlu Otopark (Lastik), Metin Elektrik (Tesisat), Acar Tesisat, Doğan Tesisat, Yılmaz Su Tesisatı, Aykar Yapı Tesisat, Işın Apt. (Su Tesisatı), Volkan Özdemir (Gitar), Kafkas Pasajı (Çalgı), Erol Saat, Kadıköy Saat Evi, Noy Saat, Moda Bisiklet

    KESİN VE İHLAL EDİLEMEZ KURALLAR:
    1. YUKARIDAKİ LİSTEDE OLMAYAN HİÇBİR İSMİ KULLANAMAZSIN. Beyoğlu, Şişli gibi Kadıköy dışı yerler önermek YASAKTIR.
    2. ASLA telefon numarası (0216 vb.) veya açık adres yazma! Sadece mekanın ismini ver.
    3. Kullanıcı "Telefonum bozuldu" derse, [ELEKTRONİK VE TELEFON] listesinden SADECE 2 tane GERÇEK isim seç.
    4. Cevabın kısa, samimi ve emojili olsun. (Örnek: "Telefonunun bozulmasına üzüldüm! Kadıköy'de bu işi çözen harika yerler var: Uğur Elektronik veya Gemici Elektrik'e gidebilirsin. 🔧")
    """

    messages = [{"role": "system", "content": system_prompt}]
    
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["text"]})
    
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": "llama3-70b-8192",  # DAHA BÜYÜK VE AKILLI MODEL! (Halüsinasyon yapmaz)
        "messages": messages,
        "temperature": 0.0,          # YARATICILIK TAMAMEN KAPALI
        "max_tokens": 200
    }

    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                 headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}, 
                                 json=payload)
        data = response.json()
        
        # Eğer Groq API limitine takılırsa hata fırlatmaması için güvenlik kontrolü
        if response.status_code == 200 and "choices" in data:
            return jsonify({"reply": data["choices"][0]["message"]["content"]})
        else:
            return jsonify({"reply": f"Groq Hatası: {data.get('error', {}).get('message', 'Bilinmeyen hata')}"})
            
    except Exception as e:
        return jsonify({"reply": f"Hata: {str(e)}"}), 500