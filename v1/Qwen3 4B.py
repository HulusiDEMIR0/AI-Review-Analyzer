import time
from ollama import chat

# Toplam süreyi başlat
toplam_baslangic = time.perf_counter()

print("[1/4] Kullanıcı yorumu hazırlanıyor...")

yorum = """
Bu telefonu yaklaşık 6 aydır kullanıyorum. Kamerası gerçekten çok güzel
ve ekran kalitesi de oldukça iyi. Bataryası ise özellikle yoğun kullanımda
çabuk bitiyor. Genel olarak telefondan memnunum ama bataryasının daha iyi
olmasını isterdim.
"""

print("[2/4] Prompt hazırlanıyor...")

prompt = f"""
Aşağıdaki kullanıcı yorumunu Türkçe olarak 2 cümleyle özetle.
Sadece özeti yaz. Başka hiçbir açıklama yapma.

Kullanıcı yorumu:
{yorum}
"""

print("[3/4] Qwen2.5 3B'ye istek gönderiliyor...")
print("Model cevap veriyor, lütfen bekleyin...\n")

# Model çağrısının başladığı zamanı kaydet
model_baslangic = time.perf_counter()

print("========== AI ÖZETİ ==========")

response = chat(
    model="qwen3:4b",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ],
    stream=True
)

# Gelen parçaları anında ekrana yaz
ilk_cevap = True

for chunk in response:

    # İlk cevap parçasının geldiği zamanı yakala
    if ilk_cevap and chunk["message"]["content"]:
        ilk_cevap_suresi = time.perf_counter() - model_baslangic
        print(f"\n[İlk çıktı: {ilk_cevap_suresi:.2f} saniye]\n")
        ilk_cevap = False

    print(chunk["message"]["content"], end="", flush=True)

print("\n===============================")

# Toplam süreyi hesapla
toplam_sure = time.perf_counter() - toplam_baslangic

print("\n[4/4] İşlem tamamlandı!")
print(f"Model cevap süresi : {time.perf_counter() - model_baslangic:.2f} saniye")
print(f"Toplam çalışma süresi: {toplam_sure:.2f} saniye")