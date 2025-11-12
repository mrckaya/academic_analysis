"""
Makine Öğrenmesi ile Yazar Etki Analizi Modülü

Bu modül, yazar istatistikleri ve ağ metriklerini kullanarak:
- Yazar etki skorları hesaplar
- Atıf sayısı tahmin modelleri eğitir
- Yazarları benzerliklerine göre kümeleme yapar
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans, DBSCAN
from sklearn.ensemble import RandomForestRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.svm import SVR
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')

# LightGBM import (opsiyonel - yoksa hata vermez)
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    print("[WARNING] LightGBM yuklu degil. 'pip install lightgbm' ile yukleyebilirsiniz.")


class MLAnalyzer:
    """
    Makine Öğrenmesi ile Yazar Etki Analizi Sınıfı
    
    Yazar istatistikleri ve ağ metriklerini birleştirerek
    yazarların etkisini ölçer ve tahmin modelleri eğitir.
    """
    
    def __init__(self, author_stats_df: pd.DataFrame, network_metrics_df: pd.DataFrame):
        """
        Args:
            author_stats_df: Yazar istatistikleri (publication_count, total_citations, h_index vb.)
            network_metrics_df: Ağ metrikleri (degree, pagerank, centrality vb.)
        """
        self.author_stats_df = author_stats_df
        self.network_metrics_df = network_metrics_df
        self.scaler = StandardScaler()  # Özellik normalizasyonu için
        self.feature_df = None  # Birleştirilmiş özellik vektörü
    
    def create_features(self) -> pd.DataFrame:
        """
        ML için özellik vektörü oluşturur
        
        Yazar istatistikleri ve ağ metriklerini birleştirerek
        makine öğrenmesi için özellik vektörü oluşturur.
        
        Returns:
            Özellik vektörünü içeren DataFrame
        """
        # Merge işleminden önce duplicate'leri kaldır
        author_stats_unique = self.author_stats_df.drop_duplicates(subset=['author_name'], keep='first')
        network_metrics_unique = self.network_metrics_df.drop_duplicates(subset=['author_name'], keep='first')
        
        # İki DataFrame'i birleştir
        merged = pd.merge(
            author_stats_unique,
            network_metrics_unique,
            on='author_name',
            how='inner'
        )
        
        # Özellikleri seç
        feature_columns = [
            'publication_count',
            'total_citations',
            'avg_citations_per_paper',
            'h_index_approx',
            'degree',
            'degree_centrality',
            'betweenness_centrality',
            'closeness_centrality',
            'eigenvector_centrality',
            'pagerank'
        ]
        
        # Eksik sütunları kontrol et
        available_features = [col for col in feature_columns if col in merged.columns]
        
        self.feature_df = merged[['author_name'] + available_features].copy()
        
        # Eksik değerleri doldur
        self.feature_df[available_features] = self.feature_df[available_features].fillna(0)
        
        # Son kontrol: duplicate'leri kaldır (güvenlik için)
        self.feature_df = self.feature_df.drop_duplicates(subset=['author_name'], keep='first')
        
        return self.feature_df
    
    def calculate_impact_score(self) -> pd.DataFrame:
        """
        Yazar etki skorunu hesaplar
        
        Çeşitli metrikleri ağırlıklı olarak birleştirerek
        her yazar için 0-100 arası etki skoru hesaplar.
        
        Ağırlıklar:
        - total_citations: 25% (en önemli)
        - h_index_approx: 20%
        - pagerank: 15%
        - publication_count: 10%
        - betweenness_centrality: 10%
        - eigenvector_centrality: 10%
        - degree_centrality: 5%
        - closeness_centrality: 5%
        
        Returns:
            Etki skorları eklenmiş DataFrame (impact_score kolonu ile)
            Sıralama: impact_score'a göre azalan
        """
        if self.feature_df is None:
            self.create_features()
        
        feature_cols = [col for col in self.feature_df.columns 
                       if col not in ['author_name']]
        
        # Özellikleri normalize et (standartlaştırma)
        X = self.feature_df[feature_cols].values
        X_scaled = self.scaler.fit_transform(X)
        
        # Ağırlıklı etki skoru hesapla
        weights = {
            'total_citations': 0.25,
            'h_index_approx': 0.20,
            'publication_count': 0.10,
            'pagerank': 0.15,
            'betweenness_centrality': 0.10,
            'eigenvector_centrality': 0.10,
            'degree_centrality': 0.05,
            'closeness_centrality': 0.05
        }
        
        impact_score = np.zeros(len(self.feature_df))
        
        # Her özelliği ağırlığıyla çarp ve topla
        for i, col in enumerate(feature_cols):
            if col in weights:
                impact_score += X_scaled[:, i] * weights[col]
        
        # Min-max normalizasyonu (0-100 arası skala)
        if impact_score.max() > impact_score.min():
            impact_score = (impact_score - impact_score.min()) / (impact_score.max() - impact_score.min()) * 100
        else:
            impact_score = np.zeros(len(impact_score))
        
        self.feature_df['impact_score'] = impact_score
        
        return self.feature_df.sort_values('impact_score', ascending=False)
    
    def predict_citations(self, test_size: float = 0.2, models: List[str] = None) -> Dict:
        """
        Atıf sayısını tahmin eden birden fazla model eğitir ve karşılaştırır
        
        Birden fazla makine öğrenmesi algoritması kullanarak yazarların toplam atıf sayılarını
        tahmin eden modeller eğitir ve performanslarını karşılaştırır.
        
        Desteklenen modeller:
        - 'rf': Random Forest Regressor
        - 'lgbm': LightGBM Regressor
        - 'dt': Decision Tree Regressor
        - 'svm': Support Vector Machine (SVR)
        
        Args:
            test_size: Test seti oranı (varsayılan: 0.2 = %20)
            models: Eğitilecek model listesi (varsayılan: ['rf', 'lgbm', 'dt', 'svm'])
            
        Returns:
            Tüm modellerin sonuçlarını içeren dict:
            - results: Her model için performans metrikleri (r2_score, rmse)
            - best_model: En iyi performans gösteren model adı
            - models: Eğitilmiş tüm modeller
            - feature_importance: En iyi modelin özellik önemleri
            - predictions: Her model için tahmin edilen değerler
            - actual: Gerçek değerler
        """
        if self.feature_df is None:
            self.create_features()
        
        # Varsayılan modeller
        if models is None:
            models = ['rf', 'lgbm', 'dt']
        
        # Özellikleri seç (total_citations ve impact_score hariç - bunlar hedef/çıktı)
        feature_cols = [col for col in self.feature_df.columns 
                       if col not in ['author_name', 'total_citations', 'impact_score']]
        
        X = self.feature_df[feature_cols].fillna(0).values
        y = self.feature_df['total_citations'].fillna(0).values
        
        # Veriyi train-test olarak ayır
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        # Özellikleri normalize et (SVM için gerekli)
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Model sonuçlarını saklamak için dict
        results = {}
        trained_models = {}
        all_predictions = {}
        
        # Her modeli eğit ve değerlendir
        for model_name in models:
            try:
                if model_name == 'rf':
                    # Random Forest Regressor
                    model = RandomForestRegressor(
                        n_estimators=100,
                        max_depth=10,
                        random_state=42,
                        n_jobs=-1
                    )
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                    feature_importance = model.feature_importances_
                    
                elif model_name == 'lgbm':
                    # LightGBM Regressor
                    if not LIGHTGBM_AVAILABLE:
                        print(f"  [WARNING] {model_name.upper()} atlandi (kutuphane yuklu degil)")
                        continue
                    model = lgb.LGBMRegressor(
                        n_estimators=100,
                        max_depth=10,
                        learning_rate=0.1,
                        random_state=42,
                        n_jobs=-1,
                        verbose=-1
                    )
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                    feature_importance = model.feature_importances_
                    
                elif model_name == 'dt':
                    # Decision Tree Regressor
                    model = DecisionTreeRegressor(
                        max_depth=10,
                        random_state=42
                    )
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                    feature_importance = model.feature_importances_
                    
                elif model_name == 'svm':
                    # Support Vector Machine (SVR)
                    model = SVR(
                        kernel='rbf',
                        C=1.0,
                        epsilon=0.1
                    )
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                    # SVM'de feature_importance yok, bu yüzden None
                    feature_importance = None
                    
                else:
                    print(f"  [WARNING] Bilinmeyen model: {model_name}")
                    continue
                
                # Model performans metrikleri
                r2 = r2_score(y_test, y_pred)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                
                results[model_name] = {
                    'r2_score': r2,
                    'rmse': rmse,
                    'model_name': model_name.upper()
                }
                trained_models[model_name] = model
                all_predictions[model_name] = y_pred
                
                print(f"  [OK] {model_name.upper()}: R^2 = {r2:.4f}, RMSE = {rmse:.2f}")
                
            except Exception as e:
                print(f"  [ERROR] {model_name.upper()} hatasi: {str(e)}")
                continue
        
        # En iyi modeli bul (R² skoruna göre)
        if results:
            best_model_name = max(results.keys(), key=lambda x: results[x]['r2_score'])
            best_model = trained_models[best_model_name]
            
            # En iyi modelin feature importance'sini al
            if hasattr(best_model, 'feature_importances_'):
                feature_importance_df = pd.DataFrame({
                    'feature': feature_cols,
                    'importance': best_model.feature_importances_
                }).sort_values('importance', ascending=False)
            else:
                feature_importance_df = pd.DataFrame({
                    'feature': feature_cols,
                    'importance': [0] * len(feature_cols)
                })
        else:
            best_model_name = None
            best_model = None
            feature_importance_df = pd.DataFrame()
        
        return {
            'results': results,
            'best_model': best_model_name,
            'models': trained_models,
            'feature_importance': feature_importance_df,
            'predictions': all_predictions,
            'actual': y_test,
            'feature_names': feature_cols
        }
    
    def cluster_authors(self, n_clusters: int = 5, method: str = 'kmeans') -> pd.DataFrame:
        """
        Yazarları benzerliklerine göre kümeleme
        
        Benzer özelliklere sahip yazarları gruplar.
        KMeans veya DBSCAN algoritması kullanılabilir.
        
        Args:
            n_clusters: Oluşturulacak küme sayısı (KMeans için)
            method: Kümeleme algoritması ('kmeans' veya 'dbscan')
            
        Returns:
            Küme bilgileri eklenmiş DataFrame (cluster, pca_1, pca_2 kolonları ile)
        """
        if self.feature_df is None:
            self.create_features()
        
        feature_cols = [col for col in self.feature_df.columns 
                       if col not in ['author_name', 'total_citations', 'impact_score']]
        
        X = self.feature_df[feature_cols].fillna(0).values
        X_scaled = self.scaler.fit_transform(X)
        
        # Küme sayısını örnek sayısına göre ayarla
        n_samples = X_scaled.shape[0]
        if n_clusters > n_samples:
            n_clusters = max(1, n_samples)
            print(f"  [WARNING] Kume sayisi ornek sayisina ({n_samples}) ayarlandi: {n_clusters}")
        
        # Kümeleme algoritması seçimi
        if method == 'kmeans':
            clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = clusterer.fit_predict(X_scaled)
        elif method == 'dbscan':
            clusterer = DBSCAN(eps=0.5, min_samples=3)
            clusters = clusterer.fit_predict(X_scaled)
        else:
            clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = clusterer.fit_predict(X_scaled)
        
        self.feature_df['cluster'] = clusters
        
        # PCA ile görselleştirme için boyut azaltma (2 boyuta indir)
        # Yüksek boyutlu özellikleri 2D'ye indirir (görselleştirme için)
        if X_scaled.shape[1] > 2:
            pca = PCA(n_components=2)
            X_pca = pca.fit_transform(X_scaled)
            self.feature_df['pca_1'] = X_pca[:, 0]
            self.feature_df['pca_2'] = X_pca[:, 1]
        else:
            # Zaten 2 veya daha az özellik varsa direkt kullan
            self.feature_df['pca_1'] = X_scaled[:, 0] if X_scaled.shape[1] >= 1 else 0
            self.feature_df['pca_2'] = X_scaled[:, 1] if X_scaled.shape[1] >= 2 else 0
        
        return self.feature_df
    
    def get_top_influential_authors(self, top_n: int = 20) -> pd.DataFrame:
        """
        En etkili yazarları döndürür
        
        Args:
            top_n: Döndürülecek yazar sayısı
            
        Returns:
            En etkili yazarları içeren DataFrame
        """
        if self.feature_df is None or 'impact_score' not in self.feature_df.columns:
            self.calculate_impact_score()
        
        # Duplicate'leri kaldır (her yazar için sadece bir satır)
        feature_df_unique = self.feature_df.drop_duplicates(subset=['author_name'], keep='first')
        
        return feature_df_unique.nlargest(top_n, 'impact_score')[
            ['author_name', 'impact_score', 'total_citations', 
             'publication_count', 'h_index_approx', 'pagerank']
        ]

