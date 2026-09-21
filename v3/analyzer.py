import json
import time
from ollama import chat


# ============================================================
# MODEL AYARLARI
# ============================================================

MODEL = "gemma3:4b"

# Gemma'nın kullandığımız context alanı
CONTEXT_SIZE = 4096

# V3 aspect analizinde yorumların bir chunk'a girmesi için
# kullanılacak yaklaşık maksimum input tokenı.
#
# 85 yorum tek chunk'a input olarak sığsa bile,
# modelin JSON çıktı üretebilmesi için daha küçük gruplar
# kullanıyoruz.
MAX_INPUT_TOKENS = 500

# Aspect + sentiment JSON çıktısı için
MAX_OUTPUT_TOKENS = 1200

# Yaklaşık token hesabı
CHARS_PER_TOKEN = 4


# ============================================================
# BAŞLANGIÇ
# ============================================================

toplam_baslangic = time.perf_counter()

print("=" * 70)
print("AI REVIEW ANALYZER - V3")
print("ASPECT + SENTIMENT ANALİZİ")
print("=" * 70)


# ============================================================
# 1. JSON DOSYASINI OKU
# ============================================================

print("\n[1/7] Yorumlar okunuyor...")

with open(
    "yorumlar.json",
    "r",
    encoding="utf-8"
) as dosya:

    veri = json.load(dosya)


yorumlar = veri["yorumlar"]

istatistikler = veri["istatistikler"]

trendyol_ai_ozet = veri.get(
    "trendyol_ai_ozet",
    ""
)

print(
    f"      Toplam yorum: {len(yorumlar)}"
)

print(
    f"      Ortalama puan: "
    f"{istatistikler['ortalama_puan']}"
)


# ============================================================
# YAKLAŞIK TOKEN HESABI
# ============================================================

def tahmini_token_sayisi(metin):
    return max(
        1,
        round(
            len(metin) / CHARS_PER_TOKEN
        )
    )


# ============================================================
# TOPLAM TAHMİNİ TOKEN SAYISI
# ============================================================

toplam_token = sum(
    tahmini_token_sayisi(
        yorum["yorum"]
    )
    for yorum in yorumlar
)

print(
    f"\n      Tahmini toplam token: {toplam_token}"
)


# ============================================================
# 2. YORUMLARI TOKEN MİKTARINA GÖRE GRUPLA
# ============================================================

print(
    "\n[2/7] Yorumlar token miktarına göre gruplandırılıyor..."
)

gruplar = []

aktif_grup = []

aktif_token = 0


for yorum in yorumlar:

    yorum_token = tahmini_token_sayisi(
        yorum["yorum"]
    )

    # Yeni yorum eklenince input sınırını aşacaksa
    # mevcut grubu kapat.
    if (
        aktif_grup
        and
        aktif_token + yorum_token
        > MAX_INPUT_TOKENS
    ):

        gruplar.append(
            aktif_grup
        )

        aktif_grup = []

        aktif_token = 0


    aktif_grup.append(
        yorum
    )

    aktif_token += yorum_token


# Son grubu ekle
if aktif_grup:

    gruplar.append(
        aktif_grup
    )


print(
    f"      Grup sayısı: {len(gruplar)}"
)


for i, grup in enumerate(
    gruplar,
    start=1
):

    grup_token = sum(
        tahmini_token_sayisi(
            yorum["yorum"]
        )
        for yorum in grup
    )

    print(
        f"      Grup {i}: "
        f"{len(grup)} yorum / "
        f"~{grup_token} token"
    )

def aspect_analizi_yap(grup):
    yorum_metni = ""
    for i, yorum in enumerate(grup, start=1):
        yorum_metni += f"[ID: {i}] Yorum: {yorum['yorum']}\n"

    prompt = f"""Sen akıllı telefon donanımları konusunda uzmanlaşmış bir yapay zeka analiz motorusun.
Aşağıdaki yorumları analiz et ve kullanıcıların görüşlerini SADECE izin verilen donanım listesindeki konulara göre sınıflandır.

İZİN VERİLEN KONU (ASPECT) LİSTESİ:
- "Kamera" (Fotoğraf, video, gece çekimi, makro)
- "Batarya" (Pil ömrü, şarjın çabuk bitmesi, hızlı şarj)
- "Ekran" (Görüntü kalitesi, parlaklık, çözünürlük)
- "Performans" (Hız, oyun performansı, donma, akıcılık)
- "Isınma" (Cihazın normal kullanımda veya oyunda ısınması)
- "Tasarım" (Malzeme kalitesi, ağırlık, renk, elde tutuş)
- "Fiyat" (Fiyat/performans oranı, ödenen paraya değmesi)

KURALLAR:
1. SADECE yukarıdaki 7 konuyu (aspect) kullanabilirsin. Asla yeni bir konu uydurma (Örn: "Telefon", "Garanti", "Samsung" yazma).
2. Kargo, kurye, paketleme, satıcı ve fatura gibi lojistik/hizmet yorumlarını KESİNLİKLE YOKSAY.
3. Eğer bir yorumda yukarıdaki listeye ait hiçbir bilgi yoksa (örn: "çok güzel", "hızlı geldi", "memnunum"), o yorumu tamamen atla ve JSON'a kesinlikle ekleme.
4. Sentiment sadece "olumlu", "olumsuz" veya "notr" olabilir.
5. Çıktını SADECE aşağıdaki JSON formatında ver. Başka hiçbir açıklama metni yazma.

JSON ŞABLONU:
{{
  "analizler": [
    {{
      "yorum_id": 1,
      "aspectler": [
        {{"konu": "Kamera", "sentiment": "olumlu"}},
        {{"konu": "Isınma", "sentiment": "olumsuz"}}
      ]
    }}
  ]
}}

YORUMLAR:
{yorum_metni}
"""
    return prompt

# ============================================================
# 4. YORUMLARI GEMMA İLE ANALİZ ET
# ============================================================

print(
    "\n[3/7] Yorumlar Gemma ile aspect/sentiment açısından analiz ediliyor..."
)

tum_analizler = []


for grup_no, grup in enumerate(
    gruplar,
    start=1
):

    print("\n" + "=" * 70)

    print(
        f"GRUP {grup_no}/{len(gruplar)}"
    )

    print(
        f"Yorum sayısı: {len(grup)}"
    )

    print("=" * 70)


    baslangic = time.perf_counter()


    response = chat(
        model=MODEL,

        messages=[
            {
                "role": "system",
                "content": (
                    "Sen profesyonel bir Türkçe "
                    "aspect-based sentiment analysis "
                    "sistemisin."
                )
            },

            {
                "role": "user",
                "content": aspect_analizi_yap(grup)
            }
        ],

        options={
            "temperature": 0.0,
            "top_p": 0.8,
            "top_k": 20,
            "repeat_penalty": 1.1,
            "num_predict": MAX_OUTPUT_TOKENS,
            "num_ctx": CONTEXT_SIZE,
            "seed": 42
        },

        format="json",

        stream=False
    )


    cevap = response[
        "message"
    ][
        "content"
    ]


    print("\nAI ANALİZİ:")

    print(cevap)


    # --------------------------------------------------------
    # Modelin JSON cevabını Python'a çevir
    # --------------------------------------------------------

    try:

        analiz_json = json.loads(
            cevap
        )

        grup_analizleri = analiz_json.get(
            "analizler",
            []
        )

        tum_analizler.extend(
            grup_analizleri
        )

        print(
            f"\n      Başarılı: "
            f"{len(grup_analizleri)} yorum analiz edildi."
        )


    except json.JSONDecodeError:

        print(
            "\nUYARI: Model geçerli JSON döndürmedi."
        )

        print(
            "Bu grup sonuçlara eklenmedi."
        )


    sure = (
        time.perf_counter()
        - baslangic
    )


    print(
        f"[Grup süresi: {sure:.2f} saniye]"
    )


# ============================================================
# 5. ASPECT + SENTIMENT İSTATİSTİĞİ
# ============================================================

print(
    "\n[4/7] Konu ve duygu istatistikleri hesaplanıyor..."
)


konular = {}


for analiz in tum_analizler:

    aspectler = analiz.get(
        "aspectler",
        []
    )


    for aspect in aspectler:

        konu = aspect.get(
            "konu"
        )

        sentiment = aspect.get(
            "sentiment"
        )


        if not konu:
            continue


        if konu not in konular:

            konular[konu] = {
                "olumlu": 0,
                "olumsuz": 0,
                "notr": 0,
                "toplam": 0
            }


        if sentiment not in [
            "olumlu",
            "olumsuz",
            "notr"
        ]:

            continue


        konular[konu][
            sentiment
        ] += 1


        konular[konu][
            "toplam"
        ] += 1


# ============================================================
# KONULARI SIKLIĞA GÖRE SIRALA
# ============================================================

sirali_konular = dict(
    sorted(
        konular.items(),
        key=lambda item: item[1]["toplam"],
        reverse=True
    )
)


# ============================================================
# ASPECT SONUÇLARINI GÖSTER
# ============================================================

print("\n" + "=" * 70)

print("ASPECT SONUÇLARI")

print("=" * 70)


for konu, bilgi in sirali_konular.items():

    print(
        f"\n{konu}"
    )

    print(
        f"  Olumlu : {bilgi['olumlu']}"
    )

    print(
        f"  Olumsuz: {bilgi['olumsuz']}"
    )

    print(
        f"  Nötr   : {bilgi['notr']}"
    )

    print(
        f"  Toplam : {bilgi['toplam']}"
    )


# ============================================================
# 6. FİNAL GEMMA PROMPTU
# ============================================================

print(
    "\n[5/7] Aspect analizlerinden detaylı ürün özeti hazırlanıyor..."
)


aspect_metin = ""


for konu, bilgi in sirali_konular.items():

    aspect_metin += (
        f"\nKONU: {konu}\n"
        f"Olumlu görüş sayısı: {bilgi['olumlu']}\n"
        f"Olumsuz görüş sayısı: {bilgi['olumsuz']}\n"
        f"Nötr görüş sayısı: {bilgi['notr']}\n"
        f"Toplam görüş sayısı: {bilgi['toplam']}\n"
    )


final_prompt = f"""
Sen profesyonel bir Türkçe ürün yorum analiz sistemisin.

Aşağıda bir ürün hakkındaki kullanıcı yorumlarından çıkarılmış
aspect ve sentiment sonuçları bulunmaktadır.

Bu verilerden yararlanarak ürün hakkında KISA, DOĞRU ve DENGELİ
bir kullanıcı değerlendirmesi oluştur.

ÇIKTI KURALLARI:
- TAM OLARAK 5 MADDE yaz.
- Her madde "-" ile başlamalıdır.
- Her madde TEK bir ana konuya odaklanmalıdır.
- Her madde TEK ve kısa bir cümle olmalıdır.
- Gereksiz ayrıntı verme.
- Aynı bilgiyi tekrar etme.
- En önemli konuları seç.
- Olumlu görüşleri belirt.
- Olumsuz görüşleri mutlaka belirt.
- Bir sorun az sayıda kullanıcı tarafından belirtilmiş olsa bile
  birden fazla yorumda tekrar ediliyorsa bunu göz ardı etme.
- Azınlık görüşünü çoğunluk görüşü gibi gösterme.
- Gerektiğinde "bazı kullanıcılar" veya "az sayıda kullanıcı"
  ifadelerini kullan.
- Bir konu hakkında olumlu ve olumsuz görüşler varsa
  iki tarafı da dengeli şekilde yansıt.
- Verilmeyen hiçbir bilgi ekleme.
- Kendi yorumunu veya tavsiyeni ekleme.
- "Alınır", "tavsiye edilir", "dikkat edilmelidir"
  gibi kendi önerilerini kullanma.
- Bir sorunun normal, kabul edilebilir veya önemsiz olduğunu
  kendin değerlendirme.
- Yorumlarda açıkça bulunmayan neden veya sonuçlar çıkarma.
- Doğal ve düzgün Türkçe kullan.
- Kelimeleri doğru yaz.
- İngilizce veya başka bir dil kullanma.
- Başlık yazma.
- 5 maddeden sonra kesinlikle başka bir şey yazma.

Ürün istatistikleri:

Toplam yorum:
{istatistikler['cekilen_yorum']}

Ortalama puan:
{istatistikler['ortalama_puan']}/5

ASPECT ANALİZİ:
{aspect_metin}

SADECE 5 MADDELİK GENEL ÜRÜN DEĞERLENDİRMESİNİ YAZ.
"""


# ============================================================
# FİNAL GEMMA
# ============================================================

final_baslangic = time.perf_counter()


response = chat(
    model=MODEL,

    messages=[
        {
            "role": "system",
            "content": (
                "Sen profesyonel bir Türkçe "
                "ürün yorum değerlendirme sistemisin."
            )
        },

        {
            "role": "user",
            "content": final_prompt
        }
    ],

    options={
        "temperature": 0.0,
        "top_p": 0.8,
        "top_k": 20,
        "repeat_penalty": 1.1,
        "num_predict": 200,
        "num_ctx": CONTEXT_SIZE,
        "seed": 42
    },

    stream=False
)


final_cevap = response[
    "message"
][
    "content"
]


final_sure = (
    time.perf_counter()
    - final_baslangic
)


# ============================================================
# SONUÇLARI GÖSTER
# ============================================================

print("\n" + "=" * 70)

print("V3 GENEL ÜRÜN YORUMU")

print("=" * 70)

print(
    final_cevap
)


# ============================================================
# TOPLAM SÜRE
# ============================================================

toplam_sure = (
    time.perf_counter()
    - toplam_baslangic
)


# ============================================================
# JSON'A KAYDEDİLECEK SONUÇ
# ============================================================

sonuc = {

    "model": MODEL,

    "urun": veri.get(
        "urun",
        {}
    ),

    "trendyol_ai_ozet": trendyol_ai_ozet,

    "istatistikler": {
        "yorum_sayisi": len(yorumlar),

        "trendyol_toplam_yorum": (
            istatistikler.get(
                "trendyol_toplam_yorum"
            )
        ),

        "trendyol_toplam_sayfa": (
            istatistikler.get(
                "trendyol_toplam_sayfa"
            )
        ),

        "cekilen_yorum": (
            istatistikler.get(
                "cekilen_yorum"
            )
        ),

        "ortalama_puan": (
            istatistikler[
                "ortalama_puan"
            ]
        ),

        "yildiz_dagilimi": (
            istatistikler[
                "yildiz_dagilimi"
            ]
        )
    },

   "tahmini_toplam_token": toplam_token,

    "context_size": CONTEXT_SIZE,

    "max_input_tokens": MAX_INPUT_TOKENS,

    "chunk_sayisi": len(gruplar),

    "aspect_analizi": sirali_konular,

    "detayli_ai_ozet": final_cevap,

    "performans": {

        "grup_sayisi": len(gruplar),

        "final_sure": round(
            final_sure,
            2
        ),

        "toplam_sure": round(
            toplam_sure,
            2
        )
    }
}


# ============================================================
# JSON'A KAYDET
# ============================================================

with open(
    "v3_analiz.json",
    "w",
    encoding="utf-8"
) as dosya:

    json.dump(
        sonuc,
        dosya,
        ensure_ascii=False,
        indent=4
    )


# ============================================================
# BİTİŞ
# ============================================================

print(
    "\nV3 sonuçları "
    "'v3_analiz.json' dosyasına kaydedildi."
)