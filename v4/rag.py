import json
import time

import chromadb
import ollama
from ollama import chat


# ============================================================
# AYARLAR
# ============================================================

EMBEDDING_MODEL = "bge-m3"
LLM_MODEL = "gemma3:4b"

CHROMA_PATH = "./v4/chroma_db"
COLLECTION_NAME = "trendyol_yorumlari"

# Kullanıcı sorusuna en yakın kaç yorum Gemma'ya gönderilecek?
TOP_K = 5


# ============================================================
# JSON DOSYASINI OKU
# ============================================================

print("=" * 70)
print("AI REVIEW ANALYZER - V4")
print("EMBEDDING + VECTOR DATABASE + RAG CHAT")
print("=" * 70)

print("\n[1/4] Ürün verileri okunuyor...")

with open(
    "./v4/yorumlar.json",
    "r",
    encoding="utf-8"
) as dosya:
    veri = json.load(dosya)

yorumlar = veri["yorumlar"]

istatistikler = veri["istatistikler"]

print(
    f"      Toplam yorum: {len(yorumlar)}"
)

print(
    f"      Ortalama puan: "
    f"{istatistikler['ortalama_puan']}/5"
)


# ============================================================
# CHROMADB'YE BAĞLAN
# ============================================================

print("\n[2/4] Vector database'e bağlanılıyor...")

client = chromadb.PersistentClient(
    path=CHROMA_PATH
)

try:
    collection = client.get_collection(
        name=COLLECTION_NAME
    )

except Exception:
    print(
        "\nHATA: ChromaDB koleksiyonu bulunamadı."
    )

    print(
        "Önce embedding oluşturma kodunu çalıştır."
    )

    exit()


print(
    f"      ChromaDB kayıt sayısı: "
    f"{collection.count()}"
)


# ============================================================
# SORUYU EMBEDDING'E ÇEVİR
# ============================================================

def soru_embedding(soru):
    response = ollama.embed(
        model=EMBEDDING_MODEL,
        input=soru # Başına hiçbir ek cümle ekleme
    )
    return response["embeddings"][0]


# ============================================================
# RAG
# ============================================================

def rag_cevapla(soru):

    # ========================================================
    # 1. SORUYU EMBEDDING'E ÇEVİR
    # ========================================================

    soru_vector = soru_embedding(soru)


    # ========================================================
    # 2. CHROMADB'DEN EN ALAKALI YORUMLARI BUL
    # ========================================================

    sonuclar = collection.query(
        query_embeddings=[soru_vector],
        n_results=TOP_K
    )

    belgeler = sonuclar["documents"][0]
    metadatalar = sonuclar["metadatas"][0]
    mesafeler = sonuclar["distances"][0]


    if not belgeler:
        return "Bu soruyla ilgili yeterli kullanıcı yorumu bulunamadı."
    
    # ========================================================
    # 3 & 4. KAYNAKLARI FİLTRELE VE GEMMA İÇİN HAZIRLA
    # ========================================================

    print("\n" + "=" * 70)
    print("KAYNAK OLARAK KULLANILAN YORUMLAR")
    print("=" * 70)

    gecerli_yorumlar = []

    for i, (yorum, metadata, mesafe) in enumerate(
        zip(belgeler, metadatalar, mesafeler),
        start=1
    ):
        # 1.2'den daha uzak (alakasız) sonuçları tamamen atla
        if mesafe > 1.2:
            continue

        puan = metadata.get("puan", "?")

        # Terminalde sadece geçerli olanları göster
        print(f"\n[{i}] ⭐ {puan}/5")
        print(f"    Benzerlik mesafesi: {mesafe:.4f}")
        print(f"    {yorum}")

        # Gemma'nın promptuna gidecek metinleri biriktir
        gecerli_yorumlar.append(
            f"\nYorum {i} ({puan}/5):\n{yorum}\n"
        )

    # Eğer filtreden geçen hiçbir yorum kalmadıysa, LLM'in uydurmasını engelle
    if not gecerli_yorumlar:
        return "Sorduğunuz konuyla ilgili yeterince alakalı kullanıcı yorumu bulunamadı."

    # Tüm geçerli yorumları tek bir metin haline getir
    yorum_metni = "".join(gecerli_yorumlar)

    # ========================================================
    # 5. GEMMA PROMPT
    # ========================================================

    prompt = f"""
Sen gerçek kullanıcı yorumlarını analiz eden Türkçe bir yapay zeka
asistanısın.

Kullanıcı şu soruyu sordu:

{soru}

Aşağıdaki yorumlar, sistem tarafından bu soruya en yakın olduğu
düşünülen kullanıcı yorumlarıdır.

ÖNCE KAYNAKLARIN ALAKALI OLUP OLMADIĞINI KONTROL ET.

ÖNEMLİ:
Yorumların retrieval sistemi tarafından getirilmiş olması,
otomatik olarak soruyla alakalı oldukları anlamına gelmez.

İLK ADIM — ALAKA KONTROLÜ:
- Kaynak yorumları kullanıcının sorusuyla karşılaştır.
- Kaynak yorumların içinde kullanıcının sorusunu doğrudan
  veya anlam olarak gerçekten ilgilendiren bilgi var mı kontrol et.
- Kaynak yorumların yalnızca genel olarak ürün hakkında olması
  yeterli değildir.
- Soruda sorulan konu hakkında gerçek bilgi bulunmalıdır.

EĞER KAYNAKLAR ALAKALI DEĞİLSE:
- Kesinlikle cevap uydurma.
- Kaynaklardaki genel ürün bilgilerini kullanarak tahminde bulunma.
- Sadece şu cevabı ver:
"Bu konuda yeterli kullanıcı yorumu bulunamadı."

EĞER KAYNAKLAR ALAKALIYSA:
- Yalnızca alakalı kaynak yorumlarına dayanarak cevap ver.
- Yorumlarda bulunmayan bilgi ekleme.
- Kendi bilgini kullanma.
- Tahmin yapma.
- Olumlu ve olumsuz görüşleri birlikte değerlendir.
- Farklı görüşler varsa bunu belirt.
- Az sayıda kullanıcı bir sorun bildirmişse bunu çoğunluk görüşü
  gibi gösterme.
- Kullanıcının sorusunu doğrudan cevapla.
- Doğal ve anlaşılır Türkçe kullan.
- Gereksiz uzun cevap verme.

ÖNEMLİ KURAL:
Bir kaynak yorumunda "sorun yok", "güzel", "memnun kaldım"
gibi genel ifadeler bulunması, bu yorumun kullanıcının sorusuna
alakalı olduğu anlamına gelmez.

Örneğin kullanıcı "Apple ürün alınır mı?" diye soruyorsa,
kaynaklarda Apple veya Apple ürünleri hakkında açık bir bilgi
yoksa kesinlikle "alınabilir" veya benzeri bir sonuç çıkarma.

KAYNAK YORUMLAR:
{yorum_metni}

ŞİMDİ ÖNCE ALAKA KONTROLÜ YAP.
KAYNAKLAR ALAKALIYSA CEVAP VER.
ALAKALI DEĞİLSE SADECE:
"Bu konuda yeterli kullanıcı yorumu bulunamadı."
YAZ.
"""

    # ========================================================
    # 6. GEMMA - STREAM
    # ========================================================

    response = chat(
        model=LLM_MODEL,

        messages=[
            {
                "role": "system",
                "content": (
                    "Sen gerçek kullanıcı yorumlarına dayalı "
                    "cevap veren bir Türkçe ürün analiz asistanısın."
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
            "num_predict": 250,
            "num_ctx": 4096,
            "seed": 42
        },

        stream=True
    )


    # ========================================================
    # 7. STREAM GELEN CEVABI EKRANA BAS
    # ========================================================

    print("\nGEMMA CEVABI")
    print("=" * 70)
    print()

    cevap = ""

    for chunk in response:

        metin = chunk["message"]["content"]

        print(
            metin,
            end="",
            flush=True
        )

        cevap += metin


    return cevap

# ============================================================
# CHAT
# ============================================================

print("\n[3/4] RAG sistemi hazır.")

print(
    "\nArtık ürün hakkında soru sorabilirsin."
)

print(
    "Çıkmak için 'q' veya 'quit' yaz."
)

print("\n" + "=" * 70)


while True:

    soru = input(
        "\nSen: "
    ).strip()


    if soru.lower() in [
        "q",
        "quit",
        "exit"
    ]:

        print(
            "\nProgram kapatılıyor..."
        )

        break


    if not soru:

        continue


    print(
        "\nAI düşünüyor..."
    )


    baslangic = time.perf_counter()


    try:

        cevap = rag_cevapla(
            soru
        )

        sure = (
            time.perf_counter()
            - baslangic
        )

        print(
            f"\n[Cevap süresi: "
            f"{sure:.2f} saniye]"
        )


    except Exception as hata:

        print(
            "\nHATA:"
        )

        print(
            hata
        )


# ============================================================
# BİTİŞ
# ============================================================

print(
    "\n[4/4] V4 RAG CHAT SONLANDI."
)