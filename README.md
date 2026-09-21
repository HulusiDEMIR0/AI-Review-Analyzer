EN 

# AI Review Analyzer

AI Review Analyzer is a step-by-step artificial intelligence project designed to analyze user reviews before purchasing a product. The system summarizes reviews, separates positive and negative opinions, analyzes user experiences under specific categories, evaluates technical specifications together with user feedback, and can compare two products when needed.

The project was developed progressively from a simple single-review summarization experiment to a RAG-based question-answering and product comparison system, structured from V1 to V6.

## General Purpose

Before buying a product, users may need to read many reviews one by one. This project aims to make that process easier and more understandable by:

- Converting user reviews into short and meaningful summaries
- Identifying repeated positive and negative points in reviews
- Analyzing categories such as camera, battery, display, performance, heating, design, and price
- Evaluating technical specifications together with user reviews
- Enabling comparison between multiple products
- Comparing RAG and single-context approaches to test answer quality across different architectures

## Project Stages

### V1 - Single Review Summarization

In the first stage, the goal was to run a local LLM through Ollama with Python and summarize a single user review.

In this version, the system:

- Sends a prepared user review to the model
- Asks the model to generate a short Turkish summary
- Tests different models in terms of speed and answer quality

V1 forms the foundation of the project by showing that communication between Python and a local LLM can be established.

Tested models:

- `qwen2.5:3b`
- `qwen3:4b`
- `gemma3:4b`

Related files:

- `v1/Qwen2.5 3B.py`
- `v1/Qwen3 4B.py`
- `v1/Gemma3.4B.py`

### V2 - Multi-Review Analysis and Summarization

In V2, the system starts analyzing multiple reviews collected from a website instead of a single review. Reviews are read from a JSON file and split into chunks to avoid exceeding the model's context limit.

In this version, the system:

- Collects review data through web scraping
- Stores reviews in JSON format
- Splits long review lists into chunks
- Generates intermediate analysis for each chunk
- Creates a general product summary from intermediate analyses

Model used:

- `gemma3:4b`

Important technical detail:

- A `4096` context size was used for Gemma
- Reviews were grouped using an approximate token calculation

Related files:

- `v2/scraper.py`
- `v2/analyzer.py`
- `v2/yorumlar.json`
- `v2/ai_analiz.json`

### V3 - Aspect-Based Sentiment Analysis

In V3, the system goes beyond general summarization and tries to understand reviews under specific aspects. At this stage, RAG was not used; reviews were directly provided to the LLM for topic and sentiment analysis.

Analyzed aspects:

- Camera
- Battery
- Display
- Performance
- Heating
- Design
- Price

In this version, the system:

- Groups reviews under specific aspect categories
- Classifies sentiment for each aspect as positive, negative, or neutral
- Produces a 5-point general product evaluation from aspect results
- Requests JSON output from the model to make results processable

Model used:

- `gemma3:4b`

Related files:

- `v3/analyzer.py`
- `v3/v3_analiz.json`

### V4 - Question Answering with RAG

In V4, RAG logic was added to the project. At this stage, reviews are converted into embeddings and stored in ChromaDB. When the user asks a question, all reviews are not sent to the model; instead, the most relevant reviews are retrieved first and then passed to the LLM.

In this version, the system:

- Converts reviews into embedding vectors
- Creates a persistent vector database with ChromaDB
- Retrieves the most relevant reviews for the user's question
- Filters irrelevant reviews using a distance threshold
- Generates answers based only on the retrieved source reviews

Models used:

- Embedding model: `bge-m3`
- Answer generation model: `gemma3:4b`

Related files:

- `v4/db_create.py`
- `v4/rag.py`
- `v4/yorumlar.json`
- `v4/chroma_db/`

### V5 - Product Comparison on Top of RAG

In V5, a product comparison mechanism was added on top of the RAG system. The system can now answer questions not only about a single product but also compare two products based on reviews and technical specifications.

In this version, the system:

- Analyzes which product or products the user question is about
- Determines whether the question is a comparison question
- Performs separate RAG searches for each product
- Retrieves relevant category data from technical specification JSON files
- Combines review data and technical data in the same context
- Generates a direct final answer for the user with an LLM

Supported products:

- Samsung Galaxy S25 FE
- iPhone 17

Models used:

- Query analysis: `gemma3:4b`
- Technical category detection: `gemma3:4b`
- Final answer generation: `qwen2.5:7b`
- Embedding/RAG infrastructure: ChromaDB and embedding-based search

Related files:

- `v5/main.py`
- `v5/query_analyzer.py`
- `v5/retrieval.py`
- `v5/technical_data.py`
- `v5/context_builder.py`
- `v5/generator1.py`
- `v5/veriler/`

### V6 - Single-Context Approach and Comparison with RAG

In V6, a single large context approach was tested as an alternative to the previous RAG structure. The goal was to compare answer quality and response time by giving all product data to the model instead of using retrieved context chunks.

In this version, the system:

- Prepares product reviews and technical data as an initial context
- Sends all relevant data to the model in a single context without using RAG
- Uses conversation memory to preserve limited question-answer continuity
- Sends the last 2 question-answer turns to resolve shortened expressions such as "this", "which one", or follow-up questions
- Enables comparison between RAG-based answers and single-context answers

Model used:

- `qwen2.5:7b`

Important technical details:

- Ollama `/api/chat` endpoint was used
- `num_ctx` was set to `32768`
- Token usage information was reported to avoid context truncation

Related files:

- `v6/main.py`
- `v6/initial_context.py`
- `v6/conversation_memory.py`
- `v6/generator.py`
- `v6/veriler/cevaplar.txt`

## Model Changes

Different models were tested at different stages of the project:

| Stage | Model(s) Used | Purpose |
| --- | --- | --- |
| V1 | `qwen2.5:3b`, `qwen3:4b`, `gemma3:4b` | Single review summarization and model testing |
| V2 | `gemma3:4b` | Multi-review summarization |
| V3 | `gemma3:4b` | Aspect and sentiment analysis |
| V4 | `bge-m3`, `gemma3:4b` | Embedding and RAG-based answer generation |
| V5 | `gemma3:4b`, `qwen2.5:7b` | Query analysis, technical category selection, and final answer generation |
| V6 | `qwen2.5:7b` | Single-context answer generation and conversation memory |

## Technologies Used

- Python
- Ollama
- Gemma
- Qwen
- BGE-M3 embedding model
- ChromaDB
- JSON-based data storage
- Web scraping
- RAG
- Prompt engineering
- Aspect-based sentiment analysis

## Folder Structure

```text
AI-Review-Analyzer/
+-- v1/   # Single review summarization and model tests
+-- v2/   # Web scraping + multi-review summarization
+-- v3/   # Aspect-based sentiment analysis
+-- v4/   # ChromaDB + embedding + RAG chat
+-- v5/   # RAG-based product comparison
+-- v6/   # Single-context + conversation memory approach
```

## Running Notes

Since this project uses local LLMs, Ollama must be installed first. The required models should also be downloaded through Ollama.

Example model download commands:

ollama pull gemma3:4b
ollama pull qwen2.5:7b
ollama pull qwen2.5:3b
ollama pull qwen3:4b
ollama pull bge-m3

Python dependencies may vary depending on the version. For RAG stages, chromadb is especially required. The project also uses requests for HTTP requests and the standard json module for data processing.

Example run command:

python v6/main.py

Some files use relative paths, so commands should be run from the project root directory.

## Development Summary

This project is an AI review analysis system that grew step by step:

1. In V1, a single review was summarized using a local LLM.
2. In V2, multiple reviews scraped from the web were summarized.
3. In V3, reviews were analyzed by topic and sentiment.
4. In V4, a RAG system was built using embeddings and a vector database.
5. In V5, technical data and product comparison were added on top of RAG.
6. In V6, a single-context approach was tested and compared with RAG.

## Goal

The final goal of this project is to create an AI-powered review analysis system that helps users make faster and more informed purchasing decisions. The system combines user reviews, technical specifications, and product comparisons to provide clearer and more organized information.


TR 

# AI Review Analyzer

AI Review Analyzer, bir urun satin alinmadan once o urun hakkindaki kullanici yorumlarini analiz etmeyi amaclayan asamali bir yapay zeka projesidir. Sistem; yorumlari ozetler, olumlu ve olumsuz gorusleri ayirir, belirli basliklar altinda kullanici deneyimini inceler, teknik ozellikleri yorumlarla birlikte degerlendirir ve ihtiyac halinde iki urunu karsilastirabilir.

Proje, tek bir yorum ozetleme denemesinden baslayip RAG tabanli soru-cevap ve urun karsilastirma sistemine kadar V1-V6 seklinde gelistirilmistir.

## Genel Amac

Kullanicilar bir urun almadan once cok sayida yorumu tek tek okumak zorunda kalabilir. Bu proje, bu sureci daha anlasilir hale getirmek icin:

- Kullanici yorumlarini kisa ve anlamli ozetlere donusturur.
- Yorumlarda tekrar eden olumlu ve olumsuz noktalari ortaya cikarir.
- Kamera, batarya, ekran, performans, isinma, tasarim ve fiyat gibi basliklarda analiz yapar.
- Teknik ozellik verilerini kullanici yorumlariyla birlikte degerlendirir.
- Birden fazla urun arasinda karsilastirma yapmaya imkan saglar.
- RAG ve tek-context yaklasimlarini karsilastirarak farkli mimarilerin cevap kalitesini test eder.

## Proje Asamalari

### V1 - Tek Yorumu Ozetleme

Ilk asamada amac, yerel bir LLM'i Ollama uzerinden Python ile calistirmak ve tek bir kullanici yorumunu ozetlemektir.

Bu surumde sistem:

- Hazir bir kullanici yorumunu modele gonderir.
- Modelden kisa ve Turkce bir ozet ister.
- Farkli modellerin hiz ve cevap kalitesini test eder.

V1, projenin temelini olusturur: Python ile yerel LLM arasinda iletisim kurulabildigini gosterir.

Kullanilan model denemeleri:

- `qwen2.5:3b`
- `qwen3:4b`
- `gemma3:4b`

Ilgili dosyalar:

- `v1/Qwen2.5 3B.py`
- `v1/Qwen3 4B.py`
- `v1/Gemma3.4B.py`

### V2 - Coklu Yorum Analizi ve Ozetleme

V2'de sistem tek yorum yerine bir internet sitesinden cekilen cok sayida yorumu analiz etmeye baslar. Yorumlar JSON dosyasindan okunur ve modelin context sinirini asmamak icin parcalara bolunur.

Bu surumde sistem:

- Web scraping ile yorum verisi toplar.
- Yorumlari JSON formatinda saklar.
- Uzun yorum listesini chunk'lara ayirir.
- Her chunk icin ara analiz uretir.
- Ara analizlerden genel urun ozeti olusturur.

Kullanilan model:

- `gemma3:4b`

Onemli teknik nokta:

- Gemma icin `4096` context kullanilmistir.
- Yorumlar yaklasik token hesabiyla gruplandirilmistir.

Ilgili dosyalar:

- `v2/scraper.py`
- `v2/analyzer.py`
- `v2/yorumlar.json`
- `v2/ai_analiz.json`

### V3 - Aspect-Based Sentiment Analysis

V3'te sistem sadece genel ozet uretmek yerine yorumlari belirli basliklar altinda anlamaya calisir. Bu asamada RAG kullanilmadan, yorumlar dogrudan LLM'e verilerek konu ve duygu analizi yapilmistir.

Analiz edilen basliklar:

- Kamera
- Batarya
- Ekran
- Performans
- Isinma
- Tasarim
- Fiyat

Bu surumde sistem:

- Yorumlari belirli aspect basliklarina ayirir.
- Her baslik icin olumlu, olumsuz veya notr duygu siniflandirmasi yapar.
- Aspect sonuclarindan 5 maddelik genel urun degerlendirmesi uretir.
- Modelden JSON formatinda cikti alarak sonuclari islenebilir hale getirir.

Kullanilan model:

- `gemma3:4b`

Ilgili dosyalar:

- `v3/analyzer.py`
- `v3/v3_analiz.json`

### V4 - RAG Sistemi ile Soru-Cevap

V4'te projeye RAG mantigi eklenmistir. Bu asamada yorumlar embedding'e donusturulup ChromaDB icinde saklanir. Kullanici bir soru sordugunda tum yorumlar modele verilmez; once soruyla en alakali yorumlar bulunur, sonra bu yorumlar LLM'e gonderilir.

Bu surumde sistem:

- Yorumlari embedding vektorlerine donusturur.
- ChromaDB uzerinde kalici vector database olusturur.
- Kullanici sorusuna en yakin yorumlari getirir.
- Alakasiz yorumlari mesafe filtresiyle eler.
- Sadece bulunan kaynak yorumlara dayanarak cevap uretir.

Kullanilan modeller:

- Embedding modeli: `bge-m3`
- Cevap uretme modeli: `gemma3:4b`

Ilgili dosyalar:

- `v4/db_create.py`
- `v4/rag.py`
- `v4/yorumlar.json`
- `v4/chroma_db/`

### V5 - RAG Uzerine Urun Karsilastirma

V5'te RAG sisteminin uzerine urun karsilastirma mekanigi eklenmistir. Sistem artik tek bir urun hakkinda cevap vermekle kalmaz; iki urunu yorumlar ve teknik ozellikler uzerinden karsilastirabilir.

Bu surumde sistem:

- Kullanici sorusunun hangi urun veya urunlerle ilgili oldugunu analiz eder.
- Sorunun karsilastirma sorusu olup olmadigini belirler.
- Her urun icin ayri RAG aramasi yapar.
- Teknik ozellik JSON dosyalarindan ilgili kategori verisini ceker.
- Yorum verisi ile teknik veriyi ayni context icinde birlestirir.
- Final LLM ile kullaniciya dogrudan cevap uretir.

Desteklenen urunler:

- Samsung Galaxy S25 FE
- iPhone 17

Kullanilan modeller:

- Sorgu analizi: `gemma3:4b`
- Teknik kategori belirleme: `gemma3:4b`
- Final cevap uretimi: `qwen2.5:7b`
- Embedding/RAG altyapisi: ChromaDB ve embedding tabanli arama

Ilgili dosyalar:

- `v5/main.py`
- `v5/query_analyzer.py`
- `v5/retrieval.py`
- `v5/technical_data.py`
- `v5/context_builder.py`
- `v5/generator1.py`
- `v5/veriler/`

### V6 - Tek Context Yaklasimi ve RAG ile Karsilastirma

V6'da onceki RAG yaklasimina alternatif olarak veriler tek bir buyuk context halinde modele verilmistir. Amac, RAG ile getirilen parca parca baglam yerine tum urun verisini modele vererek cevap kalitesini ve sureyi karsilastirmaktir.

Bu surumde sistem:

- Urun yorumlarini ve teknik verileri baslangic context'i olarak hazirlar.
- RAG kullanmadan, tum ilgili veriyi tek context icinde modele verir.
- Konusma hafizasi kullanarak onceki soru-cevap iliskisini sinirli sekilde korur.
- Son 2 soru-cevap turunu modele gondererek "peki", "hangisi", "bu" gibi eksiltili ifadeleri cozer.
- RAG sistemi ile tek-context sisteminin cevaplarini karsilastirmaya imkan saglar.

Kullanilan model:

- `qwen2.5:7b`

Onemli teknik nokta:

- Ollama `/api/chat` ucu kullanilmistir.
- `num_ctx` degeri `32768` olarak ayarlanmistir.
- Context kesilmesini onlemek icin token kullanim bilgisi raporlanmistir.

Ilgili dosyalar:

- `v6/main.py`
- `v6/initial_context.py`
- `v6/conversation_memory.py`
- `v6/generator.py`
- `v6/veriler/cevaplar.txt`

## Model Degisimleri

Proje boyunca farkli asamalarda farkli modeller denenmistir:

| Asama | Kullanilan Model(ler) | Kullanim Amaci |
| --- | --- | --- |
| V1 | `qwen2.5:3b`, `qwen3:4b`, `gemma3:4b` | Tek yorum ozetleme ve model denemesi |
| V2 | `gemma3:4b` | Coklu yorum ozetleme |
| V3 | `gemma3:4b` | Aspect ve sentiment analizi |
| V4 | `bge-m3`, `gemma3:4b` | Embedding ve RAG tabanli cevap uretimi |
| V5 | `gemma3:4b`, `qwen2.5:7b` | Sorgu analizi, teknik kategori secimi ve final cevap |
| V6 | `qwen2.5:7b` | Tek context ile cevap uretimi ve konusma hafizasi |

## Kullanilan Teknolojiler

- Python
- Ollama
- Gemma
- Qwen
- BGE-M3 embedding modeli
- ChromaDB
- JSON tabanli veri saklama
- Web scraping
- RAG
- Prompt engineering
- Aspect-based sentiment analysis

## Klasor Yapisi

```text
AI-Review-Analyzer/
+-- v1/   # Tek yorum ozetleme ve model denemeleri
+-- v2/   # Web scraping + coklu yorum ozetleme
+-- v3/   # Aspect-based sentiment analysis
+-- v4/   # ChromaDB + embedding + RAG chat
+-- v5/   # RAG tabanli urun karsilastirma
+-- v6/   # Tek context + konusma hafizasi yaklasimi
```

## Calistirma Notlari

Bu proje yerel LLM kullandigi icin once Ollama kurulmus olmalidir. Kullanilacak modellerin de Ollama uzerinden indirilmesi gerekir.

Ornek model indirme komutlari:

```bash
ollama pull gemma3:4b
ollama pull qwen2.5:7b
ollama pull qwen2.5:3b
ollama pull qwen3:4b
ollama pull bge-m3
```

Python bagimliliklari surume gore degisebilir. RAG asamalari icin ozellikle `chromadb`, HTTP istekleri icin `requests`, veri isleme icin standart `json` modulu kullanilmistir.

Ornek calistirma:

```bash
python v6/main.py
```

Bazi dosyalar goreli dosya yollari kullandigi icin komutlar proje kok dizininden calistirilmelidir.

## Projenin Gelisim Ozeti

Bu proje adim adim buyuyen bir AI review analiz sistemidir:

1. V1 ile yerel LLM'e tek yorum ozetletildi.
2. V2 ile internetten cekilen coklu yorumlar ozetlendi.
3. V3 ile yorumlar basliklara ayrilip olumlu/olumsuz analiz edildi.
4. V4 ile embedding ve vector database kullanilarak RAG sistemi kuruldu.
5. V5 ile RAG uzerine teknik veri ve urun karsilastirma mekanigi eklendi.
6. V6 ile RAG yerine tek context yaklasimi denenerek iki mimarinin cevaplari karsilastirildi.

## Hedef

Projenin nihai hedefi, kullanicinin bir urun hakkinda daha hizli ve bilincli karar verebilmesini saglayan bir yapay zeka destekli yorum analiz sistemi olusturmaktir. Sistem; yorumlari, teknik ozellikleri ve urun karsilastirmalarini bir araya getirerek kullaniciya daha anlamli ve derli toplu bilgi sunmayi hedefler.
