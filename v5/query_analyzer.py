import requests
import json


# =========================
# AYARLAR
# =========================

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3:4b"

AVAILABLE_PRODUCTS = [
    "Samsung_FE_25",
    "İphone_17"
]


# =========================
# QUERY ANALYZER
# =========================

def analyze_query(question):

    prompt = f"""
Sen bir ürün inceleme ve karşılaştırma sisteminin giriş analiz modülüsün.

Görevin, kullanıcının sorusunu analiz etmek ve sistemin bu soruyu
cevaplayıp cevaplayamayacağını belirlemektir.

Sistemde bulunan modeller:
- Samsung_FE_25
- İphone_17

ÇOK ÖNEMLİ:
Model isimlerini tahmin etme veya benzer isimleri birbirinin yerine kullanma.
Sadece kullanıcının açıkça belirttiği model adını products listesine ekle.

Örneğin:
- "Samsung FE 25" → Samsung_FE_25
- "iPhone 17" → İphone_17
- "Samsung S25" → sistemde bulunmayan model
- "Samsung S25" kesinlikle Samsung_FE_25 değildir.

Sistem; bu modeller hakkında kullanıcı yorumları, teknik özellikler,
kullanıcı deneyimleri ve modeller arasındaki karşılaştırmalar hakkında
soruları cevaplayabilir.

Kurallar:

1. Kullanıcı mevcut modellerden yalnızca birinden bahsediyorsa:
   o modeli products içine ekle.
   needs_product kesinlikle false olmalıdır.

2. Kullanıcı mevcut modellerden iki modeli karşılaştırıyorsa:
   ilgili iki modeli products içine ekle.
   comparison kesinlikle true olmalıdır.
   needs_product kesinlikle false olmalıdır.

3. Kullanıcı sistemde bulunmayan bir modeli soruyorsa:
   valid değerini false yap.
   Kullanıcının söylediği modeli başka bir mevcut modelle eşleştirme.
   needs_product false olmalıdır.

4. Kullanıcı tamamen alakasız bir soru soruyorsa:
   valid değerini false yap.
   products boş olmalıdır.
   comparison false olmalıdır.
   needs_product false olmalıdır.

5. Kullanıcı sistem kapsamında cevaplanabilecek bir konu hakkında soru
   soruyor ancak hangi modelden bahsettiğini belirtmiyorsa:

   Örnek:
   "Kamerası nasıl?"
   "Bataryası iyi mi?"
   "Ne kadar ısınıyor?"
   "Performansı nasıl?"

   Bu durumda:
   valid = true
   products = []
   comparison = false
   needs_product = true

6. Kullanıcı mevcut modellerden biri veya birkaçı hakkında
   cevaplanabilecek bir soru soruyorsa:
   valid = true
   needs_product = false

7. comparison yalnızca gerçekten iki veya daha fazla model
   karşılaştırılıyorsa true olsun.

8. Kullanıcı tek bir model hakkında soru soruyorsa:
   comparison false olsun.

9. Bir soruda iki model adı geçiyorsa ve bunlardan biri sistemde
   bulunmuyorsa, bulunan modeli diğerinin yerine koyma.
   valid false olmalıdır.

10. Sadece aşağıdaki JSON formatında cevap ver.
    JSON dışında hiçbir açıklama yazma.

JSON formatı:

{{
    "valid": true,
    "products": [],
    "comparison": false,
    "needs_product": false
}}

Kullanıcı sorusu:
{question}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
    )

    response.raise_for_status()

    result = response.json()["response"]

    result = json.loads(result)

    # --------------------------------------------------
    # PYTHON TARAFINDA KESİN KURALLAR
    # --------------------------------------------------

    products = result.get("products", [])

    # Sadece sistemde bulunan modelleri kabul et
    products = [
        product for product in products
        if product in AVAILABLE_PRODUCTS
    ]

    result["products"] = products

    # Bir veya daha fazla ürün açıkça bulunduysa
    # cihaz istemeye gerek yok
    if len(products) > 0:
        result["needs_product"] = False

    # Birden fazla ürün varsa bu bir karşılaştırmadır
    if len(products) >= 2:
        result["comparison"] = True
        result["needs_product"] = False

    # Tek ürün varsa karşılaştırma değildir
    elif len(products) == 1:
        result["comparison"] = False
        result["needs_product"] = False

    # Geçersiz soruysa cihaz isteme
    if result.get("valid") is False:
        result["needs_product"] = False

    return result


# =========================
# KULLANICI MESAJI
# =========================

def get_user_message(result):

    # Geçersiz / sistem dışında soru
    if not result.get("valid", False):
        return (
            "Bu soruya cevap veremem. "
            "Lütfen sorunuzu sistemde bulunan modeller "
            "hakkında olacak şekilde belirtin."
        )

    # Soru geçerli fakat cihaz belirtilmemiş
    if result.get("needs_product", False):
        return "Lütfen hangi cihazı kastettiğinizi belirtin."

    return None


# =========================
# TEST
# =========================

if __name__ == "__main__":
    pass