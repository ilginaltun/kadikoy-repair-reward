from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# VERİLERİ DOĞRUDAN KODA GÖMDÜK (Vercel dosya bulamama hatasını %100 engeller)
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
    history = user_data.get("history", []) 
    
    map_data = get_formatted_data()

    # HALÜSİNASYONU BİTİREN KESİN EMİRLER
    system_prompt = f"""Sen Kadıköy'deki Kentsel Tamir Ağı'nın yapay zeka asistanısın. Ilgın'a ismiyle hitap et.

GÖREVLERİN VE KESİN KURALLAR:
1. Kullanıcının sorununu dinle ve SADECE AŞAĞIDAKİ VERİLER LİSTESİNDEKİ mekanları öner.
2. DİKKAT: Kendi kafandan "Ali Bey", "Vedat Usta", "Ömer Tamirci" gibi isimler KESİNLİKLE UYDURMA.
3. Listeden soruya en uygun 2 atölyeyi seç ve enerjik, samimi bir dille yönlendirme yap. "Seni listemizdeki şu atölyelere yönlendirebilirim:" şeklinde konuş.

GERÇEK KADIKÖY TAMİRCİLERİ (SADECE BUNLARI KULLANACAKSIN):
{map_data}
"""

    messages = [{"role": "system", "content": system_prompt}]
    
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["text"]})
    
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 0.1,  # Yaratıcılığı 0.1'e çektik, artık asla uyduramaz sadece veriyi okur
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