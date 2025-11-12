"""
Uygulama yapılandırma dosyası
"""

# Veri toplama ayarları
DATA_COLLECTION = {
    'delay': 1.5,  # İstekler arası bekleme süresi (saniye)
    'max_results_per_query': 30,  # Her sorgu için maksimum sonuç
    'timeout': 30  # İstek timeout süresi (saniye)
}

# Arama sorguları (ana uygulamada kullanılacak)
DEFAULT_QUERIES = [
    "machine learning",
    "deep learning",
    "neural networks",
    "natural language processing",
    "computer vision"
]

# Veri işleme ayarları
DATA_PROCESSING = {
    'min_citations': 0,  # Minimum atıf sayısı filtresi
    'min_publications': 1  # Minimum yayın sayısı filtresi
}

# Ağ analizi ayarları
NETWORK_ANALYSIS = {
    'top_authors_for_network': 50,  # Ağ görselleştirmesi için kullanılacak yazar sayısı
    'min_coauthorships': 1,  # Minimum ortak yazarlık sayısı
    'community_algorithm': 'louvain'  # 'louvain' veya 'girvan_newman'
}

# ML analizi ayarları
ML_ANALYSIS = {
    'n_clusters': 5,  # Kümeleme için küme sayısı
    'test_size': 0.2,  # Test seti oranı
    'random_state': 42  # Rastgelelik için seed
}

# Dosya yolları
PATHS = {
    'data_dir': 'data',
    'results_dir': 'results',
    'publications_csv': 'data/publications.csv',
    'impact_scores_csv': 'results/author_impact_scores.csv',
    'network_metrics_csv': 'results/network_metrics.csv',
    'network_visualization': 'results/citation_network.png'
}

