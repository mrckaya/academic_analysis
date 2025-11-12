"""
Ana Uygulama Dosyası

Akademik Yayın Analizi ve Atıf Ağı Uygulaması

Bu uygulama:
1. Semantic Scholar API'den akademik yayın verilerini toplar
2. Verileri temizler ve yazarları çıkarır
3. Ortak yazarlık ağını oluşturur ve analiz eder
4. Makine öğrenmesi ile yazar etki skorları hesaplar
5. Sonuçları görselleştirir ve kaydeder
"""

import pandas as pd
import os
import sys
from pathlib import Path

# Proje kök dizinini path'e ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_collector import ScholarDataCollector
from src.data_processor import DataProcessor
from src.citation_network import CitationNetworkAnalyzer
from src.ml_analyzer import MLAnalyzer


def main():
    """
    Ana uygulama fonksiyonu
    
    Tüm analiz adımlarını sırayla çalıştırır:
    1. Veri toplama (Semantic Scholar API)
    2. Veri işleme ve temizleme
    3. Ortak yazarlık ağı analizi
    4. Makine öğrenmesi analizi
    5. Sonuçların kaydedilmesi
    6. Görselleştirme
    """
    
    print("=" * 60)
    print("Akademik Yayın Analizi ve Atıf Ağı Uygulaması")
    print("=" * 60)
    
    # Veri toplama
    print("\n1. VERİ TOPLAMA")
    print("-" * 60)
    
    # Semantic Scholar API ile veri toplama
    collector = ScholarDataCollector(
        api_key=None,  # Opsiyonel: API key ile rate limit artırılabilir (5000 istek/5 dakika)
        delay=3.0,     # API rate limit: 100 istek/5 dakika (her istek arası 3 saniye)
        timeout=30.0
    )
    
    # Örnek arama sorguları (kullanıcı bunları değiştirebilir)
    queries = [
        "machine learning",
        "deep learning",
        "neural networks"
    ]
    
    print(f"Toplam {len(queries)} sorgu ile arama yapılacak.")
    
    # Veri toplama - otomatik olarak dosya varsa üzerine yaz, yoksa oluştur
    csv_file = "data/publications.csv"
    os.makedirs("data", exist_ok=True)
    
    print("\nVeri toplanıyor...")
    df_publications = collector.collect_multiple_queries(
        queries, 
        max_results_per_query=50
    )
    collector.save_to_csv(df_publications, csv_file)
    
    if df_publications.empty:
        print("[WARNING] Hic veri toplanamadi!")
        return
    
    # Veri işleme
    print("\n2. VERİ İŞLEME")
    print("-" * 60)
    
    processor = DataProcessor(df_publications)
    df_cleaned = processor.clean_data()
    print(f"Temizlenmiş veri: {len(df_cleaned)} yayın")
    
    if df_cleaned.empty:
        print("[WARNING] Temizlenmis veri bos! Analiz yapilamiyor.")
        return
    
    # Yazar çıkarma
    df_authors = processor.extract_authors()
    df_authors = processor.normalize_author_names(df_authors)
    print(f"Toplam {len(df_authors)} yazar-yayın ilişkisi")
    
    if len(df_authors) == 0:
        print("[WARNING] Yazar verisi bulunamadi! Analiz yapilamiyor.")
        return
    
    # Yazar istatistikleri
    author_stats = processor.calculate_author_stats(df_authors)
    print(f"Toplam {len(author_stats)} benzersiz yazar")
    
    # En iyi yazarlar
    top_authors = processor.get_top_authors(author_stats, top_n=20)
    print("\nEn Çok Atıf Alan 10 Yazar:")
    print(top_authors[['author_name', 'total_citations', 'publication_count', 'h_index_approx']].head(10))
    
    # Atıf ağı analizi
    print("\n3. ATIF AĞI ANALİZİ")
    print("-" * 60)
    
    network_analyzer = CitationNetworkAnalyzer(df_cleaned, df_authors)
    coauthorship_graph = network_analyzer.build_coauthorship_network()
    print(f"Ağ düğüm sayısı: {len(coauthorship_graph.nodes())}")
    print(f"Ağ kenar sayısı: {len(coauthorship_graph.edges())}")
    
    # Ağ metrikleri
    network_metrics = network_analyzer.calculate_network_metrics()
    print("\nAğ Metrikleri Hesaplandı")
    
    # En çok bağlantıya sahip yazarlar
    top_connectors = network_analyzer.get_top_connectors(top_n=10)
    print("\nEn Çok Bağlantıya Sahip 10 Yazar:")
    print(top_connectors[['author_name', 'degree', 'pagerank', 'betweenness_centrality']].head(10))
    
    # Araştırma toplulukları
    communities = network_analyzer.find_research_communities()
    print(f"\n{len(communities)} araştırma topluluğu bulundu")
    
    # Makine öğrenmesi analizi
    print("\n4. MAKİNE ÖĞRENMESİ ANALİZİ")
    print("-" * 60)
    
    ml_analyzer = MLAnalyzer(author_stats, network_metrics)
    feature_df = ml_analyzer.create_features()
    print(f"Özellik vektörü oluşturuldu: {len(feature_df)} yazar")
    
    # Etki skoru hesaplama
    impact_df = ml_analyzer.calculate_impact_score()
    print("\nEn Etkili 10 Yazar (Etki Skoruna Göre):")
    top_influential = ml_analyzer.get_top_influential_authors(top_n=10)
    print(top_influential)
    
    # Atıf tahmin modelleri (birden fazla ML yöntemi ile)
    print("\nAtıf Tahmin Modelleri Eğitiliyor...")
    print("Kullanılan ML Yöntemleri: Random Forest, LightGBM, Decision Tree")
    prediction_results = ml_analyzer.predict_citations()
    
    # Tüm modellerin performanslarını göster
    print("\n[INFO] Model Performans Karsilastirmasi:")
    print("-" * 60)
    for model_name, metrics in prediction_results['results'].items():
        print(f"  {metrics['model_name']:12s} | R² = {metrics['r2_score']:7.4f} | RMSE = {metrics['rmse']:8.2f}")
    
    # En iyi modeli göster
    if prediction_results['best_model']:
        best = prediction_results['best_model']
        print(f"\n[BEST] En Iyi Model: {best.upper()}")
        print(f"   R² Skoru: {prediction_results['results'][best]['r2_score']:.4f}")
        print(f"   RMSE: {prediction_results['results'][best]['rmse']:.2f}")
    
    # En önemli özellikler
    if not prediction_results['feature_importance'].empty:
        print("\nEn Önemli Özellikler (En İyi Modele Göre):")
        print(prediction_results['feature_importance'].head(5))
    
    # Kümeleme
    print("\nYazarlar Kümelendiriliyor...")
    clustered_df = ml_analyzer.cluster_authors(n_clusters=5)
    print(f"Yazarlar {clustered_df['cluster'].nunique()} kümede gruplandı")
    
    # Sonuçları kaydet
    print("\n5. SONUÇLARIN KAYDEDİLMESİ")
    print("-" * 60)
    
    os.makedirs("results", exist_ok=True)
    
    impact_df.to_csv("results/author_impact_scores.csv", index=False)
    network_metrics.to_csv("results/network_metrics.csv", index=False)
    top_influential.to_csv("results/top_influential_authors.csv", index=False)
    clustered_df.to_csv("results/clustered_authors.csv", index=False)
    
    print("Sonuçlar 'results' klasörüne kaydedildi.")
    
    # Görselleştirme
    print("\n6. GÖRSELLEŞTİRME")
    print("-" * 60)
    
    network_analyzer.visualize_network(
        top_authors=50,
        save_path="results/citation_network.png"
    )
    print("Atıf ağı görselleştirmesi oluşturuldu.")
    
    print("\n" + "=" * 60)
    print("Analiz tamamlandı!")
    print("=" * 60)


if __name__ == "__main__":
    main()

