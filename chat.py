from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# JSON OKUMA İŞİNİ TAMAMEN İPTAL ETTİK. VERİLER DOĞRUDAN BURADA:
KADIKOY_TAMIRCILER = {
    "Elektronik": [
      "Gemici Elektrik", "Genç Elektrik", "Uğur Elektronik", 
      "Akar Elektrik", "Televizyon ve Kart Tamiri Atölyesi", "Karaca Elektrik"
    ],
    "Mobilya": [
      "Mo De Döşeme ve Mobilya", "SIR Mobilya Marangoz", "Moda Marangoz", 
      "Emir Mobilya", "Evren Mobilya", "Kadıköy Antikacılar Çarşısı"
    ],
    "Tekstil": [
      "Roventea Terzi", "Terzi Kemal", "Terzi Yakup", "Rüzgar Terzi", 
      "Dry Station", "Yağmur Terzi", "Hak Pasajı Terzileri", 
      "Jet Terzi", "Terzi Hulusi", "Terzi Bayram"
    ],
    "Ayakkabi": [
      "Moda Lostra", "Kundura Tamir", "Develi Lostra", 
      "Adliye Çarşısı Çanta/Ayakkabı Tamir"
    ],
    "Diger": [
      "Durmuşoğlu Otopark (Lastik)", "Metin Elektrik (Tesisat)", "Acar Tesisat", 
      "Doğan Tesisat", "Yılmaz Su Tesisatı", "Aykar Yapı Tesisat",
      "Işın Apt. (Su Tesisatı)", "Volkan Özdemir (Gitar Yapım/Onarım)", 
      "Kafkas Pasajı (Çalgı Tamir)", "Erol Saat", "Kadıköy Saat Evi", "Noy Saat"
    ]
}

def get_formatted_data():
    formatted = ""
    for kategori, mekanlar in KADIKOY_TAMIRCILER.items():
        formatted += f"[{kategori}]: {', '.join(mekanlar)}\n"
    return formatted

@app.route('/api/chat', methods=['POST', 'GET'])
def chat():
    if request.method == 'GET':
        return jsonify({"status": "API zehir gibi calisiyor!"})
    
    if not GROQ_API_KEY:
        return jsonify({"reply": "Sistem Hatası: API KEY eksik!"}), 500

    user_data = request.json
    user_message = user_data.get("message", "")
    history = user_data.get("history", [])[-4:] 
    
    map_data = get_formatted_data()

    # BÜYÜK MODEL İÇİN SIFIR HALÜSİNASYON PROMPTU
    system_prompt = f"""Sen Kadıköy Kentsel Tamir Ağı asistanısın. Karşındaki kişinin adı Ilgın.
        
    ELİMİZDEKİ TEK GERÇEK TAMİRCİ LİSTESİ ŞUDUR (BAŞKA HİÇBİR YER YOKTUR):
    {map_data}

    KESİN VE İHLAL EDİLEMEZ KURALLAR:
    1. YUKARIDAKİ LİSTEDE OLMAYAN HİÇBİR İSMİ KULLANAMAZSIN. 
    2. "Ayşe Tamirat", "Mehmet Ustası", "Selin Bilgisayar", "Enderoğlu" gibi isimler uydurmak KESİNLİKLE YASAKTIR.
    3. Kullanıcı "Telefonum bozuldu" veya "Elektronik" derse, [Elektronik] listesinden SADECE 2 tane GERÇEK isim seç (Örn: Uğur Elektronik veya Gemici Elektrik).
    4. Cevabın kısa, samimi ve emojili olsun.
    """

    messages = [{"role": "system", "content": system_prompt}]
    
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["text"]})
    
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": "llama3-70b-8192",  # DAHA BÜYÜK VE AKILLI MODEL! (Uydurmaz)
        "messages": messages,
        "temperature": 0.0,          # YARATICILIK TAMAMEN SIFIRLANDI!
        "max_tokens": 300
    }

    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                 headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}, 
                                 json=payload)
        data = response.json()
        
        if response.status_code == 200 and "choices" in data:
            return jsonify({"reply": data["choices"][0]["message"]["content"]})
        else:
            return jsonify({"reply": f"Groq Hatası: {data.get('error', {}).get('message', 'Bilinmeyen hata')}"})
            
    except Exception as e:
        return jsonify({"reply": f"Hata: {str(e)}"}), 500