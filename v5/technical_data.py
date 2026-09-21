import json
import requests


# ==================================================
# DOSYALAR
# ==================================================

SAMSUNG_FILE = "./v5/veriler/samsung_galaxy_s25_fe_epey.json"
IPHONE_FILE = "./v5/veriler/apple_iphone_17_epey.json"


# ==================================================
# OLLAMA
# ==================================================

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3:4b"


# ==================================================
# ÜRÜN BİLGİLERİ
# ==================================================

PRODUCT_NAMES = {
    "Samsung_FE_25": "Samsung Galaxy S25 FE",
    "İphone_17": "iPhone 17"
}


# ==================================================
# JSON YÜKLEME
# ==================================================

def load_json(file_path):

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


samsung_data = load_json(SAMSUNG_FILE)
iphone_data = load_json(IPHONE_FILE)


# ==================================================
# ÜRÜN TEKNİK VERİSİNİ GETİR
# ==================================================

def get_technical_data(product):

    if product == "Samsung_FE_25":
        return samsung_data

    elif product == "İphone_17":
        return iphone_data

    return None


# ==================================================
# TEKNİK ŞEMAYI OLUŞTUR
# ==================================================

def build_technical_schema(data):

    schema = {}

    for category, properties in data.get(
        "ozellikler",
        {}
    ).items():

        schema[category] = list(properties.keys())

    return schema


# ==================================================
# GEMMA İÇİN TEKNİK ŞEMAYI METNE ÇEVİR
# ==================================================

def schema_to_text(product_name, schema):

    lines = []

    lines.append(f"ÜRÜN: {product_name}")
    lines.append("")
    lines.append(
        "BU ÜRÜNDE BULUNAN TEKNİK ANA KATEGORİLER "
        "VE ALT ÖZELLİKLER:"
    )

    for category, properties in schema.items():

        lines.append("")
        lines.append(
            f"ANA KATEGORİ: {category}"
        )

        for property_name in properties:

            lines.append(
                f"  - {property_name}"
            )

    return "\n".join(lines)


# ==================================================
# GEMMA İLE TOPIC BELİRLEME
# ==================================================

def analyze_technical_topic(question, products):

    product_schemas = {}
    prompt_parts = []

    # --------------------------------------------------
    # ÜRÜNLERİN TEKNİK YAPILARINI HAZIRLA
    # --------------------------------------------------

    for product in products:

        data = get_technical_data(product)

        if not data:
            continue

        schema = build_technical_schema(data)

        product_schemas[product] = schema

        product_name = PRODUCT_NAMES.get(
            product,
            product
        )

        prompt_parts.append(
            schema_to_text(
                product_name,
                schema
            )
        )

    # --------------------------------------------------
    # PROMPT
    # --------------------------------------------------

    prompt = f"""
Sen bir teknik veri sınıflandırma sistemisin.

Görevin, kullanıcının sorusunun hangi TEKNİK ANA KATEGORİ
ile ilgili olduğunu belirlemektir.

Aşağıda yalnızca bu soruda kullanılacak ürünlerin GERÇEK
teknik veri yapıları verilmiştir.

ÇOK ÖNEMLİ KURALLAR:

1. "topic" olarak SADECE aşağıda
   "ANA KATEGORİ" olarak açıkça verilen kategori
   isimlerinden birini kullan veya soru teknik bir soru içermiyorsa topic = null olsun. 

2. Yeni bir kategori UYDURMA.

3. Listede bulunmayan bir kategori üretme.

4. Alt özelliklerden hiçbirini "topic" olarak döndürme.

5. Alt özellikleri mutlaka dikkate al.

6. Kullanıcının kullandığı ifade doğrudan ana kategori
   adı olmak zorunda değildir.

7. Kullanıcı bir alt özellikten bahsediyorsa,
   o alt özelliğin bulunduğu ANA KATEGORİYİ seç.

8. Sadece kelime eşleşmesine göre karar verme.
   Sorunun anlamını değerlendir.

9. Teknik bir konu yoksa veya verilen kategorilerden
   hiçbirisiyle anlamlı ilişki kurulamıyorsa:
   topic = null olsun. Buna Özellikle dikkat et. 

10. Kullanıcı teknik bir özellik sormuyorsa,
    yalnızca soruyu bir kategoriye bağlayabilmek için
    herhangi bir teknik kategori SEÇME.
    
    Örneğin:
    - fiyat
    - fiyatı ne kadar
    - kaç TL
    - güncel fiyat
    - kullanıcı memnuniyeti
    - kullanıcıların genel düşüncesi
    - satın almaya değer mi
    - genel kullanıcı deneyimi
    
    gibi sorular verilen teknik kategorilerden biriyle
    doğrudan ilişkili değilse:
    topic = null

11. Teknik bilgi üretme.

12. Verilmeyen bir kategori veya özellik hakkında
    tahmin yapma.

13. Karşılaştırma sorularında HER ÜRÜNÜ AYRI DEĞERLENDİR.

14. Bir ürün için seçtiğin topic'i diğer ürüne
    otomatik olarak kopyalama.

15. Bir ürünün teknik veri yapısında soruyla ilişkili
    kategori bulunmuyorsa o ürün için topic = null olabilir.

16. "topic" değeri olarak:
    - ürün adı
    - alt özellik adı
    - soru içerisindeki kelime
    - yeni oluşturulmuş kavram
    kullanma.

17. Teknik olmayan bir soruyu, yalnızca bir kategori
    seçmek zorunda olduğunu düşünerek teknik bir
    kategoriye zorla eşleştirme.

18. ÇIKTI SADECE GEÇERLİ JSON OLMALIDIR.

19. Açıklama yazma.

20. Markdown kullanma.

21. JSON dışında hiçbir şey döndürme.

--------------------------------------------------

ÜRÜNLERİN TEKNİK YAPILARI:

{chr(10).join(prompt_parts)}

--------------------------------------------------

KULLANICI SORUSU:

{question}

--------------------------------------------------

ÜRÜN KODLARI:

{json.dumps(products, ensure_ascii=False)}

--------------------------------------------------

ÇIKTI FORMATI:

Her ürün için mutlaka ürün KODUNU kullan.

Eğer ilgili kategori bulunamazsa:

{{
    "topics": {{
        "Samsung_FE_25": {{
            "topic": null
        }}
    }}
}}

Her ürün için ayrı sonuç üret.

Örnek:

{{
    "topics": {{
        "Samsung_FE_25": {{
            "topic": "BATARYA"
        }},
        "İphone_17": {{
            "topic": "BATARYA"
        }}
    }}
}}


"""
    
    # ==================================================
    # GEMMA
    # ==================================================

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0
            }
        },
        timeout=120
    )

    response.raise_for_status()

    result = response.json()

    raw_response = result["response"]

    print("\n" + "=" * 80)
    print("GEMMA HAM CEVABI")
    print("=" * 80)
    print(raw_response)

    try:

        gemma_result = json.loads(
            raw_response
        )

    except json.JSONDecodeError:

        return {
            "topics": {},
            "error": "Gemma geçerli JSON döndürmedi."
        }

    # ==================================================
    # PYTHON GÜVENLİK KONTROLÜ
    # ==================================================

    final_topics = {}

    gemma_topics = gemma_result.get(
        "topics",
        {}
    )

    for product in products:

        schema = product_schemas.get(
            product,
            {}
        )

        valid_categories = set(
            schema.keys()
        )

        # --------------------------------------------------
        # ÜRÜNÜ BUL
        # --------------------------------------------------

        product_result = gemma_topics.get(
            product
        )

        # Gemma ürün kodu yerine ürün adı döndürürse
        if product_result is None:

            expected_name = PRODUCT_NAMES.get(
                product
            )

            product_result = gemma_topics.get(
                expected_name
            )

        # --------------------------------------------------
        # TOPIC AL
        # --------------------------------------------------

        if isinstance(product_result, dict):

            topic = product_result.get(
                "topic"
            )

        elif isinstance(product_result, str):

            topic = product_result

        else:

            topic = None

        # --------------------------------------------------
        # TOPIC GERÇEK BİR ANA KATEGORİ Mİ?
        # --------------------------------------------------

        if topic in valid_categories:

            final_topics[product] = {
                "topic": topic
            }

        else:

            final_topics[product] = {
                "topic": None
            }

    return {
        "topics": final_topics
    }


# ==================================================
# SEÇİLEN TOPIC'İN TEKNİK VERİLERİNİ GETİR
# ==================================================

def get_topic_data(product, topic):

    data = get_technical_data(product)

    if not data:
        return None

    categories = data.get(
        "ozellikler",
        {}
    )

    # Güvenlik kontrolü
    if topic not in categories:
        return None

    return categories[topic]