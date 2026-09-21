import time
from ollama import chat

toplam_baslangic = time.perf_counter()

# ============================================================
# 5 BAĞIMSIZ KULLANICI YORUMU
# ============================================================

yorumlar = [
    """
    Bu kulaklığı yaklaşık üç aydır kullanıyorum ve şimdiye kadar oldukça
    memnun kaldım. Ses kalitesi gerçekten çok iyi, özellikle müzik dinlerken
    basları oldukça başarılı. Şarjı da beklediğimden uzun gidiyor. Kulaklık
    kulağa rahat oturuyor ve uzun süre kullandığımda herhangi bir rahatsızlık
    yaşamıyorum. Fiyatını biraz yüksek bulsam da genel olarak verdiğim paraya
    değdiğini düşünüyorum.
    """,

    """
    Bu telefonu iki haftadır kullanıyorum ancak maalesef beklentimi karşılamadı.
    Telefon özellikle oyun oynarken çok ısınıyor ve birkaç saatlik kullanımda
    bataryası neredeyse tamamen bitiyor. Kameranın gece çekimleri de oldukça kötü.
    Bunun dışında telefonun tasarımını beğeniyorum ama performans ve kamera
    konusundaki sorunlar benim için daha önemli.
    """,

    """
    Bu bilgisayarı yaklaşık bir yıldır kullanıyorum. İşlemcisi ve ekranı günlük
    kullanım için oldukça başarılı, programlar hızlı açılıyor ve ekranın renkleri
    çok güzel görünüyor. Ancak fanlar özellikle yoğun çalışırken oldukça fazla
    ses çıkarıyor. Ayrıca klavyenin bazı tuşları zaman zaman algılamıyor.
    Genel olarak bilgisayardan memnunum fakat bu iki sorun düzeltilirse çok daha
    iyi bir ürün olacağını düşünüyorum.
    """,

    """
    Ürün güzel ama fiyatı çok pahalı. Kargolama hızlıydı.
    """,

    """
    Ürünü yaklaşık sekiz aydır kullanıyorum ve ilk başta açıkçası biraz
    kararsız kalmıştım. Kurulumu oldukça kolaydı ve kutudan çıkan parçaların
    kalitesi beklediğimden daha iyiydi. İlk birkaç ay herhangi bir problem
    yaşamadım ve ürünün performansından genel olarak memnundum. Ancak son iki
    ay içerisinde cihazın zaman zaman yavaşladığını fark ettim. Özellikle aynı
    anda birkaç uygulama kullandığımda tepki vermesi birkaç saniye sürebiliyor.
    Bunun yanında cihazın tasarımını ve ekranını hâlâ çok beğeniyorum. Ekranın
    parlaklığı dışarıda kullanım için yeterli, fakat hoparlörlerin sesini biraz
    düşük buluyorum. Fiyatının piyasadaki bazı alternatiflerden daha yüksek
    olmasına rağmen genel olarak ürünü kullanmaya devam etmekten memnunum.
    Yine de performans sorunlarının ileride artıp artmayacağını merak ediyorum.
    """
]


# ============================================================
# PROMPT
# ============================================================

print("[1/5] 5 kullanıcı yorumu hazırlandı.")
print("[2/5] Prompt hazırlanıyor...")

def ozetle(yorum):
    prompt = f"""Sen profesyonel bir metin özetleme asistanısın. Aşağıdaki kullanıcı yorumunu en fazla 2 cümlelik akıcı bir Türkçe ile özetle. Kendi yorumunu katma ve sadece metindeki bilgileri kullan.

Örnek Yorum: "Ayakkabının rengi görseldeki gibi canlı geldi ve çok şık duruyor. Ancak kalıbı inanılmaz dar, bir numara büyük almama rağmen ayağımı vurdu. Kargo da çok yavaş geldi."
Örnek Özet: Kullanıcı ayakkabının görünümünü ve rengini beğenmesine rağmen, kalıbının çok dar olmasından ve kargonun yavaşlığından şikayet etmektedir.

Şimdi sıra sende. Sadece özeti yaz.

Kullanıcı Yorumu:
{yorum}

Özet:"""
    
    return prompt


# ============================================================
# YORUMLARI TEK TEK ANALİZ ET
# ============================================================

print("[3/5] Qwen2.5 3B yorumları tek tek analiz edecek...\n")

sonuclar = []

for i, yorum in enumerate(yorumlar, start=1):

    print("\n" + "=" * 60)
    print(f"YORUM {i}/5")
    print("=" * 60)

    prompt = ozetle(yorum)

    print("Model cevap veriyor...")

    baslangic = time.perf_counter()

    response = chat(
    model="gemma3:4b",
    messages=[
        {
            "role": "system",
            "content": (
                "Sen yalnızca Türkçe kullanıcı yorumlarını özetleyen "
                "bir asistansın. Her zaman doğal ve doğru Türkçe kullan."
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
        "num_predict": 150
    },
    stream=True
    )

    ilk_cevap = True
    ilk_cevap_suresi = None

    print("\n---------- AI ÖZETİ ----------")

    cevap = ""

    for chunk in response:

        metin = chunk["message"]["content"]

        if ilk_cevap and metin:
            ilk_cevap_suresi = time.perf_counter() - baslangic
            print(f"\n[İlk çıktı: {ilk_cevap_suresi:.2f} saniye]\n")
            ilk_cevap = False

        print(metin, end="", flush=True)
        cevap += metin

    cevap_suresi = time.perf_counter() - baslangic

    print("\n------------------------------")
    print(f"Yorum {i} cevap süresi: {cevap_suresi:.2f} saniye")

    sonuclar.append({
        "yorum": i,
        "ilk_cikti": ilk_cevap_suresi,
        "cevap_suresi": cevap_suresi,
        "cevap": cevap
    })


# ============================================================
# SONUÇLAR
# ============================================================

toplam_sure = time.perf_counter() - toplam_baslangic

print("\n\n" + "=" * 60)
print("[4/5] TÜM YORUMLAR TAMAMLANDI")
print("=" * 60)

for sonuc in sonuclar:
    print(
        f"Yorum {sonuc['yorum']}: "
        f"İlk çıktı = {sonuc['ilk_cikti']:.2f} sn | "
        f"Toplam = {sonuc['cevap_suresi']:.2f} sn"
    )

print("\n" + "=" * 60)
print(f"[5/5] Toplam çalışma süresi: {toplam_sure:.2f} saniye")
print("=" * 60)