# Akademik Yayın Analizi ve Atıf Ağı Uygulaması

Bu Python uygulaması, Google Scholar gibi akademik yayın veritabanlarından veri toplayarak, makine öğrenmesi kullanarak alanındaki en etkili yazarları ve araştırma grupları arasındaki bağlantıları (atıf ağı) analiz eder.

## Özellikler

- **Veri Toplama**: Google Scholar'dan yayın başlıkları, özetler, yazar isimleri ve atıf sayılarını toplar
- **Veri İşleme**: Toplanan verileri temizler ve normalize eder
- **Atıf Ağı Analizi**: Yazarlar arası ortak yazarlık ağını oluşturur ve analiz eder
- **Makine Öğrenmesi**: 
  - Yazar etki skorları hesaplar
  - Atıf sayısını tahmin eden model eğitir
  - Yazarları benzerliklerine göre kümeleme yapar
- **Görselleştirme**: Atıf ağını görsel olarak gösterir
- **Araştırma Toplulukları**: Ortak yazarlık ağından araştırma gruplarını tespit eder

## Kurulum

### Gereksinimler

- Python 3.8 veya üzeri
- pip (Python paket yöneticisi)

### Adımlar

1. **Gerekli kütüphaneleri yükleyin**:
```bash
pip install -r requirements.txt
```

## Kullanım

### Temel Kullanım

Ana uygulamayı çalıştırmak için:

```bash
python src/main.py
```

Uygulama şu adımları izler:

1. **Veri Toplama**: Google Scholar'dan belirtilen sorgularla yayınları arar
2. **Veri İşleme**: Verileri temizler ve yazar istatistiklerini hesaplar
3. **Atıf Ağı Analizi**: Ortak yazarlık ağını oluşturur ve metrikleri hesaplar
4. **Makine Öğrenmesi**: Etki skorları hesaplar ve tahmin modelleri eğitir
5. **Sonuçlar**: Sonuçları CSV dosyalarına kaydeder ve görselleştirme oluşturur

### Özelleştirme

`src/main.py` dosyasındaki arama sorgularını değiştirebilirsiniz:

```python
queries = [
    "machine learning",
    "deep learning",
    "neural networks"
]
```

## Çıktı Dosyaları

Uygulama çalıştıktan sonra şu dosyalar oluşturulur:

- `data/publications.csv`: Toplanan ham yayın verileri
- `results/author_impact_scores.csv`: Yazar etki skorları
- `results/network_metrics.csv`: Ağ metrikleri (centrality, pagerank vb.)
- `results/top_influential_authors.csv`: En etkili yazarlar
- `results/clustered_authors.csv`: Kümeleme sonuçları
- `results/citation_network.png`: Atıf ağı görselleştirmesi

## Proje Yapısı

```
.
├── src/
│   ├── __init__.py
│   ├── data_collector.py      # Google Scholar veri toplama
│   ├── data_processor.py      # Veri işleme ve temizleme
│   ├── citation_network.py    # Atıf ağı analizi
│   ├── ml_analyzer.py         # Makine öğrenmesi analizleri
│   └── main.py                # Ana uygulama
├── data/                       # Veri dosyaları (otomatik oluşturulur)
├── results/                    # Sonuç dosyaları (otomatik oluşturulur)
├── requirements.txt           # Python bağımlılıkları
└── README.md                  # Bu dosya
```

## Önemli Notlar

1. **Rate Limiting**: Google Scholar'a çok fazla istek göndermemek için istekler arasında bekleme süresi vardır.

2. **Veri Toplama**: Google Scholar'ın API'si resmi olmadığı için, veri toplama işlemi bazen yavaş olabilir veya hata verebilir.

3. **Hesaplama Süresi**: Büyük veri setlerinde ağ analizi ve ML işlemleri zaman alabilir.

## Lisans

Bu proje eğitim amaçlıdır.

