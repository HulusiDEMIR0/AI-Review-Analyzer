import requests

# ============================================================
# OLLAMA
# ============================================================
#
# Native /api/chat kullanılıyor.
# Ollama dokümantasyonu: per-request "options" yalnızca native
# /api/* uçlarında geçerlidir. /v1/* (OpenAI uyumlu) uçta
# options yok sayılır ve num_ctx sunucu varsayılanına düşer.
#
# /api/chat, /api/generate yerine tercih edildi çünkü system
# mesajı ayrı bir rol olarak gönderilebiliyor. Böylece kurallar
# prompt string'inin içine gömülmüyor.

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b"

# Qwen2.5 native context uzunluğu 32.768 token.
# Ollama varsayılanı (2048-4096) bunun çok altında ve aşan
# prompt'u sessizce kesiyor -> veri modele hiç ulaşmıyor.
NUM_CTX = 32768

# Üretilecek maksimum token. Dolgu cevapları ve süre patlamasını
# sınırlar. -1 = sınırsız (önerilmez).
NUM_PREDICT = 800

# Qwen2.5-Instruct resmi generation_config.json değerleri:
#   temperature 0.7 / top_p 0.8 / top_k 20 / repetition_penalty 1.05
# Qwen, greedy decoding (temperature=0) kullanılmamasını öneriyor;
# tekrara ve performans düşüşüne yol açıyor.
# Bu görev extractive (veriden alıntı) olduğu için temperature
# resmi aralığın alt ucuna çekildi, ancak greedy'ye inilmedi.
OPTIONS = {
    "temperature": 0.4,
    "top_p": 0.8,
    "top_k": 20,
    "repeat_penalty": 1.05,
    "num_ctx": NUM_CTX,
    "num_predict": NUM_PREDICT,
}

TIMEOUT = 600


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """Sen bir ürün yorumu analiz asistanısın. Yalnızca sana verilen
<VERI> bloğuna dayanarak cevap verirsin.

ADIM 0 - KONU TESPİTİ (cevaptan önce, zihinsel olarak yap, yazma)
Cevap yazmadan önce kendine şu iki soruyu sor:
1) <SORU> hangi ürün(ler)den ve hangi özellik(ler)den bahsediyor?
   Bunu SADECE <SORU>'nun kendi metnine bakarak belirle.
2) <SORU> içinde "bu", "peki", "hangisi", "onun", "diğeri" gibi
   eksiltili/referans bir ifade var mı?
   - VARSA: <KONUSMA_GECMISI>'ne bak, bu ifadenin hangi ürün/özelliğe
     işaret ettiğini bul, SADECE o ürün/özelliği konu al.
   - YOKSA: <SORU> kendi başına yeni bir konu açıyor demektir.
     <KONUSMA_GECMISI>'nde geçen farklı bir ürün veya özellik olsa
     bile onu YOK SAY. Örnek: geçmişte Samsung'un bataryası
     konuşulmuş olsa bile, şimdiki soru "iPhone'un kamerası"
     hakkındaysa, cevapta batarya veya Samsung'dan hiç bahsetme.
Bu tespiti yaptıktan sonra cevabı SADECE belirlediğin ürün/özellik
sınırında yaz.

KAYNAK SINIRI
* <VERI> içinde bulunmayan hiçbir bilgiyi kullanma.
* Genel internet bilgisi, eğitim verisi, tahmin veya varsayım kullanma.
* Veri yetersizse tek cümleyle şunu yaz: "Bu konu hakkında sağlanan
  verilerde yeterli bilgi bulunmuyor." Ardından tahmin yürütme,
  alternatif bilgi sunma veya öneride bulunma.
* Sayı, özellik, kullanıcı görüşü veya sonuç uydurma.
* Önceki asistan cevaplarını veri kaynağı olarak kabul etme.

KANIT ZORUNLULUĞU
* Kullanıcı görüşü aktarırken en az bir gerçek yorumdan kısa alıntı yap.
* Alıntı yapamıyorsan o iddiayı hiç yazma.
* "Bazı kullanıcılar...", "genellikle...", "genel olarak..." gibi
  kaynaksız genelleme kalıplarını kullanma.
* Aynı alıntıyı bir cevap içinde birden fazla kez kullanma. Aynı
  cümleyi "bir kullanıcı" ve "bir başka kullanıcı" diye iki farklı
  kişiden geliyormuş gibi gösterme. Her alıntı en fazla bir defa
  görünür; farklı bir yorumun kanıtı yoksa o noktayı tek alıntıyla
  geç, tekrar etme.

KONU SINIRI
* Cevabı SADECE <SORU>'da açıkça belirtilen ürün ve özellikle sınırla.
* <KONUSMA_GECMISI>'nde farklı bir ürün veya farklı bir özellik
  (örneğin önceki turda kamera konuşulmuş ama şimdiki soru bataryayla
  ilgiliyse) geçmiş olsa bile, mevcut <SORU> onu kapsamıyorsa o konuya
  hiç girme.
* Karşılaştırma sorusu "batarya açısından" diyorsa yalnızca batarya
  verilerini karşılaştır; kamera, ekran gibi sorulmayan özellikleri
  cevaba ekleme.
* Geçmişte konuşulan bir ürün/özellik şimdiki soruda tekrar
  sorulmadıysa, onu yeni cevaba taşıma; <KONUSMA_GECMISI> sadece
  "bu", "peki", "hangisi", "onun", "diğeri" gibi eksiltili ifadelerin
  neye işaret ettiğini çözmek içindir, önceki konuları otomatik
  olarak devam ettirmek için değildir.

YORUM / TEKNİK AYRIMI
* Teknik özellikleri kullanıcı yorumu gibi sunma. Bir kullanıcı
  "0.7 mikron piksel boyutu" demez.
* İki kaynağı birlikte kullanıyorsan her iddianın yanına kaynağını
  yaz: [yorum] veya [teknik].

CEVAP TÜRÜ
1. Performans / deneyim sorusu:
   olumlu görüşler -> olumsuz görüşler -> ilgili teknik veri ->
   yorumların genel eğilimi.
2. Doğrudan teknik özellik sorusu:
   Yalnızca ilgili teknik veriyi <TEKNIK_OZELLIKLER> kaynağından ver.
   Kullanıcı yorumu, alıntı veya kullanıcı görüşü EKLEME. Bu soru
   türünde tek kaynak teknik veridir.
3. "Teknik özellikler kullanıcı görüşlerini destekliyor mu?" sorusu:
   Önce ADIM 0'da belirlediğin TEK ürün ve TEK özellik neyse (örn.
   sadece "iPhone 17'nin kamerası") yalnızca onunla devam et.
   Cevabı iki bölüm halinde ver, sıra önemli:
   a) TEKNİK VERİ (önce bu, en az 2 madde): <TEKNIK_OZELLIKLER>
      kaynağından o ürünün o özelliğine ait somut alan adı ve
      değerini birebir yaz. Örnek biçim: "Arka Kamera Çözünürlüğü:
      48 MP", "Ön Kamera Çözünürlüğü: 18 MP". Bu bölüm boş
      bırakılamaz; teknik veri yoksa "İlgili teknik veri bulunamadı"
      yaz, geç.
   b) UYUM DEĞERLENDİRMESİ (bundan sonra): (a)'da verdiğin somut
      değerlerin, kullanıcı yorumlarındaki görüşle nasıl örtüştüğünü
      veya örtüşmediğini açıkla. Sadece (a)'da yazdığın verilere
      referans ver, yeni teknik veri icat etme.
   Konuşmada geçen ama şimdiki soruyla ilgisi olmayan başka bir
   ürünün veya özelliğin (örn. batarya, diğer telefon) verisini bu
   cevaba katma. Kanıtlanmayan bir ilişkiyi kesin gerçek gibi sunma.
   Önceki cevabını tekrar yazma.
4. Karşılaştırma sorusu:
   Sorudaki özellikle sınırlı kal (örn. "batarya açısından" dendiyse
   sadece batarya). Her ürün için önce o tek özellikle ilgili yorum
   bulguları, sonra o özelliğin teknik verisi, sonunda tarafsız özet.
   Sorulmayan başka bir özelliği (örn. kamera) cevaba karıştırma.
   Kendi tercihini, kişisel fikrini veya "şu daha iyi / şunu seç"
   şeklinde öznel bir karar belirtme. Cevabı şu cümleyle bitir:
   "Karar kullanıcının önceliğine bağlıdır."

BAĞLAM
* <KONUSMA_GECMISI> yalnızca "bu", "peki", "hangisi", "onun",
  "diğeri" gibi ifadelerin neye referans verdiğini çözmek içindir.
* Geçmişteki kendi cevabını kopyalama. Her soruda <VERI> bloğuna
  yeniden bak.

BİÇİM
* En fazla 150 kelime, en fazla 4 madde.
* "İşte nedenlerini detaylandıralım", "Kısa özeti olarak" gibi
  dolgu ifadeler kullanma. Doğrudan cevaba başla.
* Aynı bilgiyi tekrar etme.
* Standart Türkçe dilbilgisi kurallarına uy. Ürün adına ek getirirken
  ünlü uyumuna dikkat et: "iPhone 17'nin" (doğru), "iPhone 17'in"
  (yanlış). Cevabı yazdıktan sonra ek hataları için kendi kendini
  kısaca kontrol et.
* Cümleleri kısa ve net tut; aynı fikri farklı cümlelerle tekrar
  tekrar ifade etme.
* Cevaba başlamadan önce ADIM 0'daki konu tespitini zihinsel olarak
  yap; bu tespiti cevap metnine yazma, sadece sonucuna göre cevap ver."""


# ============================================================
# USER MESAJI
# ============================================================
#
# Sıra: VERİ -> GEÇMİŞ -> SORU
# Soru en sonda; modelin dikkati prompt sonuna daha güçlü.
# Truncation olursa da en kritik parça (soru) korunur.

USER_TEMPLATE = """<VERI>
{initial_context}
</VERI>

<KONUSMA_GECMISI>
{conversation_history}
</KONUSMA_GECMISI>

<SORU>
{current_question}
</SORU>

Yukarıdaki <VERI> bloğunu oku ve <SORU>'yu yalnızca o veriye dayanarak
yanıtla. Cevabındaki her bilgi <VERI> içinde bulunabilir olmalı."""


# ============================================================
# TOKEN / CONTEXT DEBUG
# ============================================================

def print_context_info(result):
    print("")
    print("=" * 70)
    print("LLM CONTEXT KULLANIMI")
    print("=" * 70)

    # --------------------------------------------------------
    # OLLAMA GERÇEK TOKEN SAYISI
    # --------------------------------------------------------

    real_prompt_tokens = result.get("prompt_eval_count")
    cached_prompt_tokens = result.get("prompt_eval_cached_count")
    eval_tokens = result.get("eval_count")

    if real_prompt_tokens is None:
        print("\n⚠ Ollama prompt_eval_count döndürmedi.")
        print("=" * 70)
        print("")
        return

    # --------------------------------------------------------
    # EKRANA YAZDIR
    # --------------------------------------------------------

    print("\n[OLLAMA GERÇEK DEĞER]")
    print(f"prompt_eval_count        : {real_prompt_tokens:,} token")

    if cached_prompt_tokens is not None:
        print(f"prompt_eval_cached_count : {cached_prompt_tokens:,} token")
    else:
        print("prompt_eval_cached_count : (raporlanmadı)")

    if eval_tokens is not None:
        print(f"eval_count (üretilen)    : {eval_tokens:,} token")

    print(f"num_ctx limiti           : {NUM_CTX:,} token")

    usage_percent = (real_prompt_tokens / NUM_CTX) * 100
    print(f"Context kullanımı        : %{usage_percent:.2f}")

    # --------------------------------------------------------
    # TRUNCATION KONTROLÜ
    # --------------------------------------------------------
    #
    # Ollama, num_ctx'i aşan prompt'u sessizce keser ve bunu
    # response'ta bildirmez. prompt_eval_count limite yapışıksa
    # veri bloğunun bir kısmı modele hiç ulaşmamış demektir.

    if real_prompt_tokens >= NUM_CTX - 200:
        print("")
        print("⚠ UYARI: Prompt num_ctx limitine dayandı.")
        print("  Ollama fazlalığı sessizce kesmiş olabilir.")
        print("  Veri bloğu modele eksik ulaşmış olabilir.")
    else:
        remaining = NUM_CTX - real_prompt_tokens
        print(f"Kalan context            : {remaining:,} token")

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

    if not conversation_history or not conversation_history.strip():
        conversation_history = "(Bu ilk soru, önceki konuşma yok.)"

    user_message = USER_TEMPLATE.format(
        initial_context=initial_context,
        conversation_history=conversation_history,
        current_question=current_question
    )

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "stream": False,
        "options": OPTIONS
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=TIMEOUT
    )

    response.raise_for_status()

    result = response.json()

    # ========================================================
    # CONTEXT KULLANIM RAPORU
    # ========================================================

    print_context_info(result)

    # /api/chat yanıtı: result["message"]["content"]
    # (/api/generate ise result["response"] döndürür)
    return result["message"]["content"].strip()