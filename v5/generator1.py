import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"


def generate_answer(context_text):
    """
    Context Builder tarafından oluşturulan context'i
    Gemma'ya gönderir ve nihai cevabı döndürür.
    """

    prompt =  f"""
Sen bir ürün karşılaştırma asistanısın.

Kullanıcının sorusuna SADECE aşağıdaki CONTEXT içindeki bilgilere dayanarak cevap ver.

{context_text}

KURALLAR:

1. Önce kullanıcının sorusunu doğru anla.
2. Soruda hangi ürünlerden bahsediliyorsa SADECE o ürünleri kullan.
3. Birden fazla ürün varsa ürünleri birbirine karıştırma.
4. Karşılaştırma sorusuysa iki ürünü ayrı ayrı değerlendir ve sonuç olarak kullanıcsını sorusuna uygun bir cevap ver 
5. Tek ürün sorusuysa sadece o ürünü cevapla.
6. Kullanıcı sadece belirli bir konu soruyorsa sadece o konu hakkında cevap ver.
7. Context'te olmayan hiçbir bilgi uydurma.
8. Kullanıcı yorumlarını teknik özellik gibi gösterme.
9. Teknik özellikleri kullanıcı yorumu gibi gösterme.
10. Kullanıcı fiyat sormadıysa fiyat hakkında konuşma.
11. Kullanıcı genel bir inceleme istemediyse telefon hakkında genel inceleme yapma.
12. Cevabı doğrudan soruya ver. Gereksiz başlıklar ve uzun bölümler oluşturma.
13. Sonuç net olabiliyorsa net bir sonuç ver.

ÖNEMLİ:

Context içinde her ürün kendi adı altında ayrı bir bölümdedir.
Bir ürünün verisini başka ürüne aitmiş gibi kullanma. karşılaştrırma sorusu sorduğunda ürünlerin özelliklerini bir üründe toplama

CEVAP:
"""

    payload = {
    "model": MODEL,
    "prompt": prompt,
    "stream": False,
    "options": {
        "temperature": 0.1,
        "num_ctx": 8192,
        "top_p": 0.9
      }
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=180
    )

    response.raise_for_status()

    result = response.json()

    return result["response"].strip()