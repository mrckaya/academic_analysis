# 🎓 Akademik Yayın Analizi ve Atıf Ağı Projesi

**Makine Öğrenmesi ile Yazar Etki Analizi ve Network Analizi**

Bu Python uygulaması, **Semantic Scholar API** kullanarak akademik yayın verilerini toplayıp, makine öğrenmesi ve network analizi teknikleri ile alanındaki en etkili yazarları belirler ve araştırma grupları arasındaki bağlantıları analiz eder.

## ✨ Özellikler

- **📡 API Entegrasyonu**: Semantic Scholar API ile otomatik veri toplama (rate limiting ve retry mekanizması ile)
- **🧹 Veri İşleme**: Pandas ile kapsamlı veri temizleme, normalizasyon ve yazar istatistikleri hesaplama
- **🕸️ Network Analizi**: NetworkX ile ortak yazarlık ağı analizi (PageRank, centrality metrikleri)
- **🤖 Makine Öğrenmesi**: 
  - **Çoklu ML Modelleri**: Random Forest, LightGBM, Decision Tree ile model karşılaştırması
  - Yazar etki skorları hesaplama (0-100 arası)
  - Atıf sayısı tahmin modelleri (en iyi model otomatik seçilir)
  - Yazarları benzerliklerine göre kümeleme (KMeans, DBSCAN)
- **📊 Görselleştirme**: Profesyonel ağ görselleştirmeleri (matplotlib)
- **👥 Araştırma Toplulukları**: Louvain algoritması ile araştırma gruplarını tespit etme

## 🚀 Kurulum

### Gereksinimler

- Python 3.8 veya üzeri
- pip (Python paket yöneticisi)
- İnternet bağlantısı (API erişimi için)

### Adımlar

1. **Repository'yi klonlayın:**
```bash
git clone https://github.com/mrckaya/academic_analysis.git
cd academic_analysis
```

2. **Gerekli kütüphaneleri yükleyin:**
```bash
pip install -r requirements.txt
```

**Not:** LightGBM yüklenmesi biraz zaman alabilir. Eğer sorun yaşarsanız:
```bash
pip install lightgbm --no-cache-dir
```

## 📖 Kullanım

### Temel Kullanım

Ana uygulamayı çalıştırmak için:

```bash
python src/main.py
```

Uygulama şu adımları otomatik olarak izler:

1. **Veri Toplama**: Semantic Scholar API'den belirtilen sorgularla yayınları arar
2. **Veri İşleme**: Verileri temizler, yazarları çıkarır ve istatistiklerini hesaplar (H-index dahil)
3. **Network Analizi**: Ortak yazarlık ağını oluşturur ve metrikleri hesaplar (PageRank, centrality)
4. **Makine Öğrenmesi**: 
   - Özellik vektörleri oluşturur
   - Etki skorları hesaplar
   - 3 farklı ML modeli eğitir ve karşılaştırır (RF, LGBM, DT)
   - En iyi modeli otomatik seçer
   - Yazarları kümeleme yapar
5. **Sonuçlar**: Sonuçları CSV dosyalarına kaydeder ve görselleştirme oluşturur

### Özelleştirme

**Arama Sorgularını Değiştirme:**

`src/main.py` dosyasındaki arama sorgularını değiştirebilirsiniz:

```python
queries = [
    "machine learning",
    "deep learning",
    "neural networks",
    "natural language processing"  # Yeni sorgu ekle
]
```

**API Key Kullanma (Rate Limit Artırma):**

Semantic Scholar API key ile rate limit 100'den 5000 istek/5 dakika'ya çıkar:

```python
collector = ScholarDataCollector(
    api_key="YOUR_API_KEY",  # https://www.semanticscholar.org/product/api adresinden alın
    delay=3.0,
    timeout=30.0
)
```

**Görselleştirme Ayarları:**

```python
network_analyzer.visualize_network(
    top_authors=50,           # Gösterilecek yazar sayısı
    min_edge_weight=2,        # Minimum bağlantı ağırlığı
    save_path="results/citation_network.png"
)
```

## 📁 Çıktı Dosyaları

Uygulama çalıştıktan sonra `results/` klasöründe şu dosyalar oluşturulur:

- `author_impact_scores.csv`: Tüm yazarlar için etki skorları ve metrikler
- `network_metrics.csv`: Ağ analizi metrikleri (PageRank, centrality vb.)
- `top_influential_authors.csv`: En etkili 20 yazarın özet bilgileri
- `clustered_authors.csv`: Kümeleme sonuçları (benzer yazarlar gruplandırılmış)
- `citation_network.png`: Ortak yazarlık ağı görselleştirmesi

## 🏗️ Proje Yapısı

```
academic_analysis/
├── src/
│   ├── __init__.py
│   ├── data_collector.py      # Semantic Scholar API veri toplama
│   ├── data_processor.py      # Veri işleme ve istatistik hesaplama
│   ├── citation_network.py    # Network analizi ve görselleştirme
│   ├── ml_analyzer.py         # ML modelleri (RF, LGBM, DT) ve etki skoru
│   └── main.py                # Ana uygulama orkestrasyonu
├── data/
│   └── publications.csv       # Toplanan ham veriler (otomatik oluşturulur)
├── results/                   # Sonuç dosyaları (otomatik oluşturulur)
│   ├── citation_network.png
│   ├── author_impact_scores.csv
│   ├── network_metrics.csv
│   ├── top_influential_authors.csv
│   └── clustered_authors.csv
├── requirements.txt           # Python bağımlılıkları
├── config.py                  # Yapılandırma dosyası
├── PRESENTATION.md            # Detaylı proje sunumu
└── README.md                  # Bu dosya
```

## 📊 Model Performansı

Gerçek veri seti ile alınan sonuçlar:

| Model | R² Skoru | RMSE | Açıklama |
|-------|----------|------|----------|
| **LightGBM** | **0.7600** | **9332.00** | 🏆 En iyi performans (Gradient Boosting) |
| Random Forest | 0.7251 | 9988.18 | Ensemble yöntemi, iyi performans |
| Decision Tree | 0.6595 | 11115.87 | Basit model, daha düşük performans |

**Not:** R² = 0.76, veri varyansının %76'sını açıklıyor. Bu, akademik literatürde "iyi" kabul edilen bir değerdir.

## 🔧 Teknik Detaylar

### Kullanılan Teknolojiler

- **API**: Semantic Scholar API v1
- **Veri İşleme**: Pandas 2.2+, NumPy 1.26+
- **Network Analizi**: NetworkX 3.2.1, Python-Louvain 0.16
- **Makine Öğrenmesi**: Scikit-learn 1.4+, LightGBM 4.1+
- **Görselleştirme**: Matplotlib 3.9+

### Sistem Gereksinimleri

- **Python**: 3.8+
- **RAM**: Minimum 4GB (önerilen: 8GB+)
- **Disk**: 500MB (veriler ve sonuçlar için)
- **İnternet**: API erişimi için

## 📝 Önemli Notlar

1. **Rate Limiting**: Semantic Scholar API rate limit: 100 istek/5 dakika (API key ile: 5000 istek/5 dakika). Sistem otomatik olarak rate limit'e uyar.

2. **Veri Toplama**: API entegrasyonu ile güvenilir veri toplama. Retry mekanizması ve exponential backoff ile hata yönetimi sağlanır.

3. **Hesaplama Süresi**: 
   - Veri toplama: Sorgu başına ~30-60 saniye (rate limit nedeniyle)
   - Veri işleme: 1000 yayın için < 1 saniye
   - Network analizi: 500 düğüm için < 10 saniye
   - ML model eğitimi: 3 model için < 10 saniye

4. **Duplicate Kontrolü**: Sistem, duplicate yazarları ve yayınları otomatik olarak temizler.

## 📚 Daha Fazla Bilgi

Detaylı proje sunumu için `PRESENTATION.md` dosyasına bakabilirsiniz. Bu dosyada:
- Kod örnekleri ve açıklamaları
- Algoritma detayları
- Görselleştirme örnekleri
- Performans metrikleri
- Gelecek iyileştirmeler

bulunmaktadır.

## 🤝 Katkıda Bulunma

Bu proje açık kaynak kodludur ve katkılara açıktır. Pull request'ler memnuniyetle karşılanır!

## 📄 Lisans

Bu proje eğitim amaçlıdır.

## 🔗 Referanslar

- **Semantic Scholar API**: https://www.semanticscholar.org/product/api
- **NetworkX Dokümantasyonu**: https://networkx.org/
- **Scikit-learn Dokümantasyonu**: https://scikit-learn.org/
- **LightGBM Dokümantasyonu**: https://lightgbm.readthedocs.io/

---

**⭐ Projeyi beğendiyseniz yıldız vermeyi unutmayın!**
