import requests

# ============================================================
# OLLAMA
# ============================================================

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"
NUM_CTX = 8192

# ============================================================
# TOKEN / CONTEXT DEBUG
# ============================================================

def print_context_info(
    result
):
    print("")
    print("=" * 70)
    print("LLM CONTEXT KULLANIMI")
    print("=" * 70)

    # --------------------------------------------------------
    # OLLAMA GERÇEK TOKEN SAYISI
    # --------------------------------------------------------

    real_prompt_tokens = result.get("prompt_eval_count")
    cached_prompt_tokens = result.get("prompt_eval_cached_count")

    # --------------------------------------------------------
    # EKRANA YAZDIR
    # --------------------------------------------------------

    if real_prompt_tokens is not None:

        print("\n[OLLAMA GERÇEK DEĞER]")

        print(f"prompt_eval_count        : {real_prompt_tokens:,} token")
        print(f"prompt_eval_cached_count : {cached_prompt_tokens:,} token")

        print(
            f"num_ctx limiti      : "
            f"{NUM_CTX:,} token"
        )

        usage_percent = (
            real_prompt_tokens / NUM_CTX
        ) * 100

        print(
            f"Context kullanımı   : "
            f"%{usage_percent:.2f}"
        )

        if real_prompt_tokens > NUM_CTX:
            print(
                "⚠ UYARI: Prompt num_ctx limitini aşıyor!"
            )

        else:
            remaining = NUM_CTX - real_prompt_tokens

            print(
                f"Kalan context      : "
                f"{remaining:,} token"
            )

    else:

        print(
            "\n⚠ Ollama prompt_eval_count döndürmedi."
        )

    print("=" * 70)
    print("")


# ============================================================
# ANSWER GENERATOR
# ============================================================

def generate_answer(
    initial_context,
    conversation_history,
    current_question
):

    prompt = f"""
Sen, yalnızca sana verilen veriler ve konuşma geçmişine dayanarak
cevap veren bir analiz ve karşılaştırma asistanısın.

VERİ KURALI

* Başlangıç context'inde bulunmayan hiçbir bilgiyi kullanma.
* Genel internet bilgisi, eğitim verisi, tahmin veya varsayım kullanma.
* Veri yeterli değilse bilgi uydurma; açıkça "Bu konu hakkında
  sağlanan verilerde yeterli bilgi bulunmuyor." de.
* Sayı, özellik, kullanıcı görüşü veya sonuç uydurma.
* Önceki asistan cevaplarını gerçek veri kaynağı olarak kabul etme.

BAĞLAM

* Konuşma geçmişini "bu", "peki", "hangisi", "onun", "diğeri"
  gibi ifadelerin neye referans verdiğini anlamak için kullan.
* Önceki konuşmadaki ürünü ve konuyu koru; ancak gerçek bilgiyi
  her zaman başlangıç context'inden al.

CEVAP TÜRÜ

1. Performans / deneyim sorusu:

   * Kullanıcıların olumlu görüşleri
   * Kullanıcıların olumsuz görüşleri
   * Soruyla ilgili teknik veriler
   * Yorumların genel eğilimi ve bunun veride görülen nedeni
     şeklinde cevap ver.

2. Doğrudan teknik özellik sorusu:

   * Yalnızca sorulan konuyla ilgili teknik verileri ver.
   * Kullanıcı yorumlarını ve ilgisiz teknik özellikleri ekleme.

3. Teknik özelliklerin kullanıcı görüşlerini destekleyip
   desteklemediği sorulursa:

   * Yalnızca ilgili teknik verileri kullan.
   * Teknik verinin kullanıcı görüşüyle uyumlu olup olmadığını
     açıkla.
   * Kanıtlanmayan bir ilişkiyi kesin gerçek gibi sunma.

4. Karşılaştırma sorusu:

   * Her ürün için önce kullanıcı yorumlarında öne çıkan
     olumlu/olumsuz noktaları ver.
   * Ardından yalnızca soruyla ilgili teknik verileri ver.
   * Sonunda bu bilgileri birlikte, tarafsız biçimde özetle.
   * Kendi tercihini, kişisel fikrini veya "şu daha iyi/şunu seç"
     şeklinde öznel bir karar verme.

GENEL KURALLAR

* Sorulan konuya odaklan; gereksiz bilgi ekleme.
* Aynı bilgiyi tekrar etme.
* Teknik verileri kullanıcı görüşleriyle karıştırma.
* Kullanıcı yorumlarında bulunmayan bir görüşü yorumlara atfetme.
* Yorumlardan güvenilir biçimde çıkarılabiliyorsa genel eğilimi
  belirt; yeterli veri yoksa bunu belirt.
* Cevabı doğrudan ve gereksiz uzatmadan ver.

============================================================
BAŞLANGIÇ CONTEXT
=================

{initial_context}

============================================================
KONUŞMA GEÇMİŞİ
===============

{conversation_history}

============================================================
KULLANICI SORUSU
================

{current_question}

============================================================
CEVAP
=====

"""


    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_ctx": NUM_CTX,
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

    # ========================================================
    # CONTEXT KULLANIM RAPORU
    # ========================================================

    print_context_info(
        result=result
    )

    return result["response"].strip()