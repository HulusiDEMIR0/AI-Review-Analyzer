import json
import time
from turtle import speed
from matplotlib.pylab import seed
from ollama import chat


MODEL = "gemma3:4b"

# ============================================================
# BİLGİSAYARA GÖRE AYARLAR
# ============================================================

# Gemma'yı Ollama'da 4096 context ile çalıştırıyoruz.
CONTEXT_SIZE = 4096

# Context'in tamamını yorumlarla doldurmuyoruz.
# Prompt + cevap için alan bırakıyoruz.
MAX_INPUT_TOKENS = 3000

# Modelin üretebileceği maksimum cevap uzunluğu.
MAX_OUTPUT_TOKENS = 500

# Token sayısını yaklaşık hesaplamak için kullanılan katsayı.
# Türkçe için yaklaşık bir değer olarak kullanıyoruz.
CHARS_PER_TOKEN = 4


toplam_baslangic = time.perf_counter()


# ============================================================
# YAKLAŞIK TOKEN HESABI
# ============================================================

def tahmini_token_sayisi(metin):
    """
    Metnin yaklaşık token sayısını hesaplar.

    Not:
    Bu gerçek Gemma tokenizer'ı değildir.
    V2'de chunk boyutunu güvenli belirlemek için yaklaşık hesap yapıyoruz.
    """

    return max(
        1,
        round(len(metin) / CHARS_PER_TOKEN)
    )


# ============================================================
# JSON DOSYASINI OKU
# ============================================================

print("=" * 70)
print("AI REVIEW ANALYZER - V2.2")
print("ÇOKLU YORUM + CHUNKING + GEMMA")
print("=" * 70)

print("\n[1/7] Yorumlar okunuyor...")

with open(
    "yorumlar.json",
    "r",
    encoding="utf-8"
) as dosya:

    veri = json.load(dosya)


yorumlar = veri["yorumlar"]
istatistikler = veri["istatistikler"]
trendyol_ai_ozet = veri.get("trendyol_ai_ozet", "")

print(f"      Toplam yorum: {len(yorumlar)}")
print(
    f"      Ortalama puan: "
    f"{istatistikler['ortalama_puan']}"
)


# ============================================================
# TÜM YORUMLARIN TOKEN MİKTARINI HESAPLA
# ============================================================

print("\n[2/7] Toplam token miktarı hesaplanıyor...")

toplam_token = 0

for yorum in yorumlar:

    metin = yorum["yorum"]

    toplam_token += tahmini_token_sayisi(
        metin
    )


print(
    f"      Tahmini toplam token: "
    f"{toplam_token}"
)

print(
    f"      Kullanılacak context: "
    f"{CONTEXT_SIZE}"
)

print(
    f"      Bir chunk için maksimum giriş: "
    f"{MAX_INPUT_TOKENS} token"
)


# ============================================================
# TOKEN'A GÖRE CHUNK OLUŞTUR
# ============================================================

print("\n[3/7] Yorumlar token miktarına göre gruplandırılıyor...")

chunks = []
aktif_chunk = []
aktif_token = 0


for yorum in yorumlar:

    yorum_token = tahmini_token_sayisi(
        yorum["yorum"]
    )

    # Eğer mevcut chunk'a bu yorum sığmıyorsa
    if (
        aktif_chunk
        and aktif_token + yorum_token
        > MAX_INPUT_TOKENS
    ):

        chunks.append(
            aktif_chunk
        )

        aktif_chunk = []
        aktif_token = 0


    aktif_chunk.append(
        yorum
    )

    aktif_token += yorum_token


# Son chunk
if aktif_chunk:

    chunks.append(
        aktif_chunk
    )


print(
    f"      Oluşturulan chunk sayısı: "
    f"{len(chunks)}"
)

for i, chunk in enumerate(
    chunks,
    start=1
):

    chunk_token = sum(
        tahmini_token_sayisi(
            yorum["yorum"]
        )
        for yorum in chunk
    )

    print(
        f"      Chunk {i}: "
        f"{len(chunk)} yorum / "
        f"~{chunk_token} token"
    )


# ============================================================
# GRUP ÖZETLEME FONKSİYONU
# ============================================================

def grup_ozetle(chunk):

    yorum_metni = ""

    for i, yorum in enumerate(
        chunk,
        start=1
    ):
        yorum_metni += (
            f"\nYorum {i} "
            f"({yorum['puan']}/5):\n"
            f"{yorum['yorum']}\n"
        )

    prompt = f"""
Aşağıdaki kullanıcı yorumlarını birlikte analiz et.

Bu yorumlar aynı ürün hakkındadır.

Görevin, yorum grubundaki bilgileri mümkün olduğunca kısa
ama bilgi kaybı olmadan özetlemektir.

Kurallar:
- Yalnızca verilen yorumlardaki bilgileri kullan.
- Bilgi uydurma.
- Yorumlarda olmayan özellikler ekleme.
- Önemli olumlu noktaları belirt.
- Önemli olumsuz noktaları mutlaka belirt.
- Bir sorun az sayıda kullanıcı tarafından dile getirilse bile,
  birden fazla yorumda tekrar ediliyorsa görmezden gelme.
- Bir konu çoğunluk tarafından olumlu değerlendirilse bile,
  aynı konuda olumsuz deneyimler varsa bunları da belirt.
- Azınlık görüşlerini çoğunluk görüşü gibi gösterme.
- Azınlıkta kalan sorunları "bazı kullanıcılar" veya
  "az sayıda kullanıcı" şeklinde ifade et.
- Ortak görüşleri önceliklendir.
- Gereksiz ayrıntıları ve tekrarları çıkar.
- Kısa, yoğun ve bilgi açısından dolu bir metin oluştur.
- En fazla 3 kısa cümle kullan.
- Doğal ve düzgün Türkçe kullan.
- Anlamı değiştirme.
- Sadece analizi yaz.

YORUMLAR:
{yorum_metni}

ARA ANALİZ:
"""

    return prompt


# ============================================================
# CHUNK'LARI GEMMA'YA GÖNDER
# ============================================================

print("\n[4/7] Yorumlar Gemma ile analiz ediliyor...")

ara_ozetler = []

# ============================================================
# TEK CHUNK VARSA
# DOĞRUDAN FİNAL ÖZETE GEÇECEĞİZ
# ============================================================

if len(chunks) == 1:

    print("      Tek chunk bulundu.")
    print("      Ara özet oluşturulmayacak.")
    print("      Yorumlar doğrudan final analize gönderilecek.")

    ara_ozetler = []


# ============================================================
# BİRDEN FAZLA CHUNK VARSA
# ARA ÖZETLER OLUŞTUR
# ============================================================

else:

    for grup_index, chunk in enumerate(
        chunks,
        start=1
    ):

        print("\n" + "=" * 70)

        print(
            f"CHUNK {grup_index}/{len(chunks)}"
        )

        print(
            f"Yorum sayısı: {len(chunk)}"
        )

        print("=" * 70)

        prompt = grup_ozetle(chunk)

        baslangic = time.perf_counter()

        response = chat(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Sen profesyonel bir Türkçe "
                        "kullanıcı yorum analiz sistemisin."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={
                "temperature": 0.0,
                "top_p": 0.8,
                "top_k": 20,
                "repeat_penalty": 1.1,
                "num_predict": 150,
                "num_ctx": CONTEXT_SIZE,
                "seed": 42
            },
            stream=True
        )

        cevap = ""

        for chunk_data in response:

            metin = chunk_data["message"]["content"]

            print(
                metin,
                end="",
                flush=True
            )

            cevap += metin

        sure = (
            time.perf_counter()
            - baslangic
        )

        print(
            f"\n\n[Chunk süresi: "
            f"{sure:.2f} saniye]"
        )

        ara_ozetler.append(
            cevap
        )

# ============================================================
# ARA ÖZETLERİ BİRLEŞTİR
# ============================================================

# ============================================================
# 5/7 - ANALİZ EDİLECEK VERİYİ HAZIRLA
# ============================================================

print("\n" + "=" * 70)
print("[5/7] Final analiz için veri hazırlanıyor...")
print("=" * 70)


# Eğer bütün yorumlar tek chunk'a sığıyorsa
# ara özetleri kullanmayacağız.
if len(chunks) == 1:

    print("      Tek chunk bulundu.")
    print("      Ara özet kullanılmayacak.")
    print("      Yorumların tamamı doğrudan final analize gönderilecek.")

    final_veri = ""

    for i, yorum in enumerate(
        yorumlar,
        start=1
    ):

        final_veri += (
            f"\nYorum {i} "
            f"({yorum['puan']}/5):\n"
            f"{yorum['yorum']}\n"
        )


# Birden fazla chunk varsa
# 4/7'de oluşturduğumuz ara özetleri kullanacağız.
else:

    print(
        f"      {len(chunks)} chunk bulundu."
    )

    print(
        "      Ara özetler final analize gönderilecek."
    )

    ara_metin = ""

    for i, ozet in enumerate(
        ara_ozetler,
        start=1
    ):

        ara_metin += (
            f"\n\nGRUP {i} ANALİZİ:\n"
            f"{ozet}"
        )

    final_veri = ara_metin

# ============================================================
# FİNAL PROMPT
# ============================================================

final_prompt = f"""
Sen profesyonel bir Türkçe kullanıcı yorumu analiz sistemisin.

Görevin, aşağıdaki kullanıcı yorumlarını analiz ederek ürün hakkında
KISA ve BİLGİ YOĞUN bir genel değerlendirme oluşturmaktır.

ÇIKTI KURALLARI:
1. TAM OLARAK 5 MADDE yaz.
2. Her madde '-' işaretiyle başlamalıdır.
3. Her maddede yalnızca BİR ana konu ele alınmalıdır.
4. Her madde TEK ve kısa bir cümle olmalıdır.
5. Her cümle mümkün olduğunca kısa ve doğal Türkçe olmalıdır.
6. Gereksiz ayrıntıları, tekrarları ve örnekleri çıkar.
7. Yorumlarda en sık tekrar eden olumlu noktaları öne çıkar.
8. Yorumlarda birden fazla kişi tarafından belirtilen olumsuz
   noktaları mutlaka belirt.
9. Az sayıda kullanıcı tarafından belirtilen ancak gerçek bir sorun
   oluşturan noktaları da belirt; fakat bunları çoğunluğun görüşü gibi gösterme.
10. "Bazı kullanıcılar", "az sayıda kullanıcı" veya
    "bazı yorumlarda" ifadelerini gerektiğinde kullan.
11. Yorumlarda bulunmayan hiçbir bilgi ekleme.
12. Kendi yorumunu, tavsiyeni veya önerini ekleme.
13. "Alınır", "tavsiye edilir", "dikkat edilmeli" gibi kişisel
    değerlendirmeler yapma.
14. Türkçe yazım, noktalama ve dilbilgisine dikkat et.
15. İngilizce, Çince, Korece veya başka bir dil kullanma.
16. Bir özelliğin hem olumlu hem olumsuz görüşleri varsa,
    önemli olan iki tarafı da dengeli biçimde yansıt.
17. Yalnızca en önemli 5 sonucu seç.
18. 5 maddeden sonra KESİNLİKLE hiçbir şey yazma.
19. Başlık, açıklama, sonuç veya ek metin yazma.

ÇIKTI FORMATI TAM OLARAK ŞU YAPIYA BENZEMELİDİR:

- Kullanıcıların çoğu ...
- Telefonun ... özelliği ...
- Bazı kullanıcılar ...
- Genel olarak ...
- Bazı yorumlarda ...

Ürün istatistikleri:

Toplam yorum:
{istatistikler['cekilen_yorum']}

Ortalama puan:
{istatistikler['ortalama_puan']}/5

ANALİZ EDİLECEK VERİ:
{final_veri}

ŞİMDİ SADECE 5 MADDEYİ YAZ.
"""
# ============================================================
# FİNAL GEMMA ÇAĞRISI
# ============================================================

print("\n" + "=" * 70)

print(
    "[6/7] Genel ürün özeti oluşturuluyor..."
)

print("=" * 70)

final_baslangic = time.perf_counter()


response = chat(
    model=MODEL,
    messages=[
        {
            "role": "system",
            "content": (
                "Sen profesyonel bir Türkçe "
                "ürün değerlendirme sistemisin."
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
        "num_predict": MAX_OUTPUT_TOKENS,
        "num_ctx": CONTEXT_SIZE
    },
    stream=True
)


final_cevap = ""


print("\nGENEL AI ÜRÜN ÖZETİ")
print("-" * 70)


for chunk_data in response:

    metin = chunk_data["message"]["content"]

    print(
        metin,
        end="",
        flush=True
    )

    final_cevap += metin


final_sure = (
    time.perf_counter()
    - final_baslangic
)


# ============================================================
# SONUÇ
# ============================================================

toplam_sure = (
    time.perf_counter()
    - toplam_baslangic
)


print("\n\n" + "=" * 70)

print("[7/7] V2.2 TAMAMLANDI")

print("=" * 70)

print(
    f"\nToplam yorum      : "
    f"{len(yorumlar)}"
)

print(
    f"Tahmini token     : "
    f"{toplam_token}"
)

print(
    f"Chunk sayısı      : "
    f"{len(chunks)}"
)

print(
    f"Final analiz süresi: "
    f"{final_sure:.2f} saniye"
)

print(
    f"Toplam çalışma    : "
    f"{toplam_sure:.2f} saniye"
)


# ============================================================
# SONUCU KAYDET
# ============================================================

sonuc = {

    "model": MODEL,

    "urun": veri.get("urun", {}),

    "trendyol_ai_ozet": trendyol_ai_ozet,

    "yorum_sayisi": len(yorumlar),

    "tahmini_toplam_token": toplam_token,

    "context_size": CONTEXT_SIZE,

    "chunk_sayisi": len(chunks),

    "ortalama_puan": (
        istatistikler["ortalama_puan"]
    ),

    "yildiz_dagilimi": istatistikler.get(
        "yildiz_dagilimi",
        {}
    ),

    "ara_ozetler": ara_ozetler,

    "genel_ozet": final_cevap,

}


with open(
    "ai_analiz.json",
    "w",
    encoding="utf-8"
) as dosya:

    json.dump(
        sonuc,
        dosya,
        ensure_ascii=False,
        indent=4
    )


print(
    "\nSonuçlar "
    "'ai_analiz.json' dosyasına kaydedildi."
)