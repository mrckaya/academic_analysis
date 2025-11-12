"""
Ortak Yazarlık Ağı Analizi ve Görselleştirme Modülü

Bu modül, yazarlar arası ortak yazarlık ilişkilerini analiz eder:
- Ortak yazarlık ağı oluşturur
- Ağ metrikleri hesaplar (PageRank, centrality vb.)
- Araştırma topluluklarını tespit eder
- Ağı görselleştirir
"""

import networkx as nx
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict
import matplotlib.pyplot as plt


class CitationNetworkAnalyzer:
    """
    Ortak Yazarlık Ağı Analizi Sınıfı
    
    Yazarlar arası ortak çalışma ilişkilerini analiz eder ve görselleştirir.
    """
    
    def __init__(self, publications_df: pd.DataFrame, authors_df: pd.DataFrame):
        """
        Args:
            publications_df: Yayın verilerini içeren DataFrame
            authors_df: Yazar-yayın ilişkilerini içeren DataFrame (normalize edilmiş)
        """
        self.publications_df = publications_df
        self.authors_df = authors_df
        self.coauthorship_graph = nx.Graph()  # Ortak yazarlık ağı
    
    def build_coauthorship_network(self) -> nx.Graph:
        """
        Yazarlar arası ortak yazarlık ağını oluşturur
        
        Aynı yayında birlikte yazmış yazarlar arasında bağlantı (edge) oluşturur.
        Edge ağırlığı, yazarların birlikte yazdığı yayın sayısını gösterir.
        
        Returns:
            Ortak yazarlık ağı (NetworkX Graph)
        """
        self.coauthorship_graph = nx.Graph()
        
        # Her yayındaki yazarları işle
        for idx, row in self.publications_df.iterrows():
            authors = row.get('authors', [])
            
            # En az 2 yazar olmalı (ortak yazarlık için)
            if not authors or len(authors) < 2:
                continue
            
            # Yazar isimlerini normalize et (küçük harf, boşluk temizleme)
            normalized_authors = []
            for author in authors:
                if isinstance(author, str):
                    normalized = author.lower().strip()
                    normalized = normalized.replace('  ', ' ')
                    normalized_authors.append(normalized)
            
            # Her yazar çifti arasında edge oluştur
            # Örnek: [A, B, C] -> (A-B), (A-C), (B-C) bağlantıları
            for i in range(len(normalized_authors)):
                for j in range(i + 1, len(normalized_authors)):
                    author1 = normalized_authors[i]
                    author2 = normalized_authors[j]
                    
                    if self.coauthorship_graph.has_edge(author1, author2):
                        # Edge zaten varsa, ağırlığı artır (ortak yayın sayısı)
                        self.coauthorship_graph[author1][author2]['weight'] += 1
                        self.coauthorship_graph[author1][author2]['publications'].append(
                            row.get('title', '')
                        )
                    else:
                        # Yeni edge oluştur
                        self.coauthorship_graph.add_edge(
                            author1, 
                            author2,
                            weight=1,  # İlk ortak yayın
                            publications=[row.get('title', '')]
                        )
        
        return self.coauthorship_graph
    
    def calculate_network_metrics(self) -> pd.DataFrame:
        """
        Ağ metriklerini hesaplar
        
        Her yazar için ağdaki önemini ölçen metrikler:
        - degree: Direkt bağlantı sayısı
        - degree_centrality: Normalize edilmiş bağlantı sayısı
        - betweenness_centrality: Ağdaki köprü rolü
        - closeness_centrality: Diğer yazarlara yakınlık
        - eigenvector_centrality: Önemli yazarlarla bağlantı
        - pagerank: Genel önem skoru
        
        Returns:
            Yazar metriklerini içeren DataFrame
        """
        if len(self.coauthorship_graph.nodes()) == 0:
            self.build_coauthorship_network()
        
        metrics = []
        
        # Ağ metriklerini hesapla
        degree_centrality = nx.degree_centrality(self.coauthorship_graph)
        betweenness_centrality = nx.betweenness_centrality(self.coauthorship_graph)
        closeness_centrality = nx.closeness_centrality(self.coauthorship_graph)
        eigenvector_centrality = nx.eigenvector_centrality(
            self.coauthorship_graph, 
            max_iter=1000
        )
        pagerank = nx.pagerank(self.coauthorship_graph)
        
        # Yazar istatistikleri ile birleştir
        for node in self.coauthorship_graph.nodes():
            degree = self.coauthorship_graph.degree(node)
            
            metrics.append({
                'author_name': node,
                'degree': degree,
                'degree_centrality': degree_centrality.get(node, 0),
                'betweenness_centrality': betweenness_centrality.get(node, 0),
                'closeness_centrality': closeness_centrality.get(node, 0),
                'eigenvector_centrality': eigenvector_centrality.get(node, 0),
                'pagerank': pagerank.get(node, 0)
            })
        
        metrics_df = pd.DataFrame(metrics)
        
        # author_name kolonunu korumak için kopyala
        author_names = metrics_df['author_name'].copy()
        
        # Yazar istatistikleri ile birleştir
        # ÖNEMLİ: authors_df'de aynı yazar için birden fazla satır olabilir (yazar-yayın ilişkileri)
        # Bu yüzden önce unique yazarları almalıyız
        if 'author_normalized' in self.authors_df.columns:
            # author_normalized kolonunu geçici olarak author_name olarak kullan
            authors_for_merge = self.authors_df.copy()
            
            # Eğer author_name zaten varsa, onu kaldır (çakışmayı önlemek için)
            if 'author_name' in authors_for_merge.columns:
                authors_for_merge = authors_for_merge.drop(columns=['author_name'])
            
            # author_normalized'i author_name olarak rename et
            authors_for_merge = authors_for_merge.rename(columns={'author_normalized': 'author_name'})
            
            # Aynı yazar için birden fazla satır olabilir - unique yazarları al
            # Her yazar için ilk satırı al (veya aggregate yap)
            authors_unique = authors_for_merge.drop_duplicates(subset=['author_name'], keep='first')
            
            merged = pd.merge(
                metrics_df,
                authors_unique,
                on='author_name',
                how='left',
                suffixes=('', '_from_authors')
            )
        elif 'author_name' in self.authors_df.columns:
            # author_name varsa direkt merge et, ama önce unique yazarları al
            authors_unique = self.authors_df.drop_duplicates(subset=['author_name'], keep='first')
            
            merged = pd.merge(
                metrics_df,
                authors_unique,
                on='author_name',
                how='left',
                suffixes=('', '_from_authors')
            )
        else:
            merged = metrics_df
        
        # author_name kolonunun varlığını garanti et
        if 'author_name' not in merged.columns:
            merged['author_name'] = author_names.values[:len(merged)]
        
        # Son kontrol: duplicate'leri kaldır (güvenlik için)
        merged = merged.drop_duplicates(subset=['author_name'], keep='first')
        
        return merged
    
    def find_research_communities(self, algorithm: str = 'louvain') -> Dict:
        """
        Araştırma topluluklarını bulur
        
        Benzer araştırma yapan yazarları gruplar.
        Topluluk tespiti için Louvain veya Girvan-Newman algoritması kullanılır.
        
        Args:
            algorithm: Topluluk tespit algoritması ('louvain' veya 'girvan_newman')
            
        Returns:
            Topluluk ID'sine göre yazar listelerini içeren dict
            Örnek: {0: ['author1', 'author2'], 1: ['author3', 'author4']}
        """
        if len(self.coauthorship_graph.nodes()) == 0:
            self.build_coauthorship_network()
        
        # Algoritma seçimi
        if algorithm == 'louvain':
            try:
                import community as community_louvain
                communities = community_louvain.best_partition(self.coauthorship_graph)
            except ImportError:
                print("python-louvain kütüphanesi bulunamadı. Girvan-Newman algoritması kullanılıyor.")
                communities = self._girvan_newman_communities()
        elif algorithm == 'girvan_newman':
            communities = self._girvan_newman_communities()
        else:
            communities = self._girvan_newman_communities()
        
        # Topluluk bilgilerini organize et: {topluluk_id: [yazar_listesi]}
        community_dict = defaultdict(list)
        for node, comm_id in communities.items():
            community_dict[comm_id].append(node)
        
        return dict(community_dict)
    
    def _girvan_newman_communities(self) -> Dict:
        """
        Girvan-Newman algoritması ile topluluk bulma
        
        Edge betweenness'e göre toplulukları ayırır.
        
        Returns:
            {node: community_id} formatında dict
        """
        communities_generator = nx.community.girvan_newman(self.coauthorship_graph)
        
        # İlk iterasyonu al (en iyi bölünme)
        top_level_communities = next(communities_generator)
        
        communities = {}
        for i, comm in enumerate(top_level_communities):
            for node in comm:
                communities[node] = i
        
        return communities
    
    def get_top_connectors(self, top_n: int = 20) -> pd.DataFrame:
        """
        En çok bağlantıya sahip yazarları döndürür
        
        Args:
            top_n: Döndürülecek yazar sayısı
            
        Returns:
            En çok bağlantıya sahip yazarları içeren DataFrame
        """
        metrics_df = self.calculate_network_metrics()
        # Duplicate'leri kaldır (her yazar için sadece bir satır)
        metrics_df = metrics_df.drop_duplicates(subset=['author_name'], keep='first')
        top_connectors = metrics_df.nlargest(top_n, 'degree')
        return top_connectors
    
    def visualize_network(
        self, 
        top_authors: int = 30,  # Daha az düğüm - daha okunabilir
        figsize: Tuple[int, int] = (24, 16),
        node_size_factor: float = 800,
        save_path: str = None,
        min_edge_weight: int = 2  # Sadece güçlü bağlantıları göster
    ):
        """Ağı görselleştirir - Sadeleştirilmiş ve okunabilir versiyon"""
        if len(self.coauthorship_graph.nodes()) == 0:
            self.build_coauthorship_network()
        
        # En önemli yazarları seç (PageRank'e göre - daha iyi önem ölçüsü)
        metrics_df = self.calculate_network_metrics()
        # Duplicate'leri kaldır (güvenlik için)
        metrics_df = metrics_df.drop_duplicates(subset=['author_name'], keep='first')
        top_authors_list = metrics_df.nlargest(top_authors, 'pagerank')['author_name'].tolist()
        
        # Alt grafi oluştur
        subgraph = self.coauthorship_graph.subgraph(top_authors_list).copy()
        
        if len(subgraph.nodes()) == 0:
            print("[WARNING] Gorsellestirme icin yeterli dugum yok!")
            return
        
        # Zayıf kenarları filtrele (sadece güçlü bağlantıları göster)
        edges_to_remove = [(u, v) for u, v, d in subgraph.edges(data=True) 
                           if d.get('weight', 1) < min_edge_weight]
        subgraph.remove_edges_from(edges_to_remove)
        
        # İzole düğümleri kaldır
        isolated = list(nx.isolates(subgraph))
        subgraph.remove_nodes_from(isolated)
        
        if len(subgraph.nodes()) == 0:
            print("[WARNING] Filtreleme sonrasi dugum kalmadi!")
            return
        
        # Toplulukları bul (renklendirme için)
        try:
            import community.community_louvain as community_louvain
            communities = community_louvain.best_partition(subgraph)
        except:
            # community modülü yoksa, degree'e göre grupla
            communities = {}
            degrees = dict(subgraph.degree())
            sorted_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
            num_communities = min(10, len(sorted_nodes))
            for idx, (node, _) in enumerate(sorted_nodes):
                communities[node] = idx % num_communities
        
        # Renk paleti (daha canlı renkler)
        import matplotlib.cm as cm
        num_communities = len(set(communities.values()))
        colors = cm.Set3(np.linspace(0, 1, max(num_communities, 1)))
        node_colors = [colors[communities.get(node, 0) % len(colors)] for node in subgraph.nodes()]
        
        # Layout - Daha iyi dağılım için (daha fazla boşluk)
        try:
            pos = nx.spring_layout(subgraph, k=3, iterations=200, weight='weight', seed=42)
        except:
            try:
                pos = nx.kamada_kawai_layout(subgraph, weight='weight')
            except:
                pos = nx.spring_layout(subgraph, k=2, iterations=100)
        
        # Çizim
        fig, ax = plt.subplots(figsize=figsize, facecolor='white')
        
        # Node boyutları (sadece PageRank'e göre - daha anlamlı)
        pagerank_values = nx.pagerank(subgraph)
        max_pr = max(pagerank_values.values()) if pagerank_values.values() else 1
        
        node_sizes = []
        for node in subgraph.nodes():
            pr = pagerank_values.get(node, 0)
            # PageRank'e göre boyut (normalize edilmiş)
            size = (pr / max_pr) * node_size_factor + 300  # Minimum 300
            node_sizes.append(size)
        
        # Edge ağırlıkları ve renkleri
        edges = subgraph.edges()
        weights = [subgraph[u][v].get('weight', 1) for u, v in edges]
        max_weight = max(weights) if weights else 1
        
        # Kenarları çiz (önce, böylece node'lar üstte kalır)
        # Sadece güçlü bağlantıları daha kalın göster
        edge_widths = [min(w / max_weight * 3, 2.5) for w in weights]
        
        nx.draw_networkx_edges(
            subgraph,
            pos,
            width=edge_widths,
            alpha=0.3,  # Daha şeffaf - daha az dikkat dağıtıcı
            edge_color='#888888',
            style='solid',
            ax=ax
        )
        
        # En önemli node'ları belirle (PageRank'e göre)
        important_nodes = sorted(pagerank_values.items(), key=lambda x: x[1], reverse=True)[:15]
        important_node_names = [node for node, _ in important_nodes]
        
        # Node'ları çiz - önemli node'lar daha belirgin
        node_colors_final = []
        node_edge_widths = []
        for node in subgraph.nodes():
            if node in important_node_names:
                node_colors_final.append('#FF6B6B')  # Kırmızı - önemli
                node_edge_widths.append(3.0)
            else:
                node_colors_final.append(node_colors[list(subgraph.nodes()).index(node)])
                node_edge_widths.append(1.5)
        
        nx.draw_networkx_nodes(
            subgraph, 
            pos, 
            node_size=node_sizes,
            node_color=node_colors_final,
            alpha=0.85,
            edgecolors='black',
            linewidths=node_edge_widths,
            ax=ax
        )
        
        labels = {}
        for node in important_node_names:
            if node in subgraph.nodes():
                name_parts = str(node).split()
                if len(name_parts) > 1:
                    label = name_parts[-1].upper()  # Son isim, büyük harf
                else:
                    label = str(node)[:12].upper()
                labels[node] = label
        
        # Etiketleri çiz - sadece önemli node'lar için (daha okunabilir)
        for node, label in labels.items():
            x, y = pos[node]
            # Önemli yazarlar için daha belirgin etiket
            ax.text(x, y, label, 
                   fontsize=12,
                   ha='center', va='center',
                   bbox=dict(boxstyle='round,pad=0.6', 
                           facecolor='#FFE5E5',  # Açık kırmızı arka plan
                           edgecolor='#FF6B6B',  # Kırmızı kenar
                           linewidth=2,
                           alpha=0.95),
                   fontweight='bold',
                   color='#8B0000')  # Koyu kırmızı yazı
        
        # Ana başlık - Projenin ne yaptığını açıkça belirt
        main_title = 'AKADEMİK YAYIN ANALİZİ: ORTAK YAZARLIK AĞI'
        subtitle = f'Bu görsel, {len(subgraph.nodes())} akademisyenin birbirleriyle yaptığı ortak çalışmaları gösterir'
        
        ax.text(0.5, 0.98, main_title,
               transform=ax.transAxes,
               fontsize=24, fontweight='bold',
               ha='center', va='top',
               color='#1a1a1a')
        
        ax.text(0.5, 0.94, subtitle,
               transform=ax.transAxes,
               fontsize=14,
               ha='center', va='top',
               color='#555555',
               style='italic')
        
        # Açıklayıcı bilgi kutusu - Sol üst
        info_text = (
            '[INFO] AG ISTATISTIKLERI\n'
            f'• {len(subgraph.nodes())} Akademisyen\n'
            f'• {len(subgraph.edges())} Ortak Çalışma\n'
            f'• {num_communities} Araştırma Grubu'
        )
        ax.text(0.02, 0.88, info_text,
               transform=ax.transAxes,
               fontsize=12,
               verticalalignment='top',
               bbox=dict(boxstyle='round,pad=1.0', 
                        facecolor='#E8F4F8', 
                        edgecolor='#2C5F7D', 
                        linewidth=2, 
                        alpha=0.95),
               color='#1a1a1a')
        
        # Legend/Efsane - Sağ üst
        legend_text = (
            '🔴 KIRMIZI DAİRELER\n'
            'En önemli 15 akademisyen\n'
            '(PageRank skoruna göre)\n\n'
            '🔵 RENKLİ DAİRELER\n'
            'Diğer akademisyenler\n'
            '(Araştırma gruplarına göre\n'
            'renklendirilmiş)\n\n'
            '📏 DAİRE BOYUTU\n'
            'Ne kadar büyükse,\n'
            'o kadar önemli\n'
            '(PageRank skoruna göre)\n\n'
            '➖ ÇİZGİLER\n'
            'Ortak yayın sayısı\n'
            '(Kalın = Daha fazla)'
        )
        ax.text(0.98, 0.88, legend_text,
               transform=ax.transAxes,
               fontsize=11,
               verticalalignment='top',
               ha='right',
               bbox=dict(boxstyle='round,pad=1.0', 
                        facecolor='#FFF9E6', 
                        edgecolor='#D4A574', 
                        linewidth=2, 
                        alpha=0.95),
               color='#1a1a1a')
        
        # Alt açıklama - Alt kısım
        footer_text = (
            'Bu analiz, akademik yayınlardan toplanan verilerle oluşturulmuştur. '
            'Her daire bir akademisyeni, her çizgi ortak çalışmayı temsil eder.'
        )
        ax.text(0.5, 0.02, footer_text,
               transform=ax.transAxes,
               fontsize=11,
               ha='center', va='bottom',
               style='italic',
               color='#666666',
               bbox=dict(boxstyle='round,pad=0.5', 
                        facecolor='#F5F5F5', 
                        edgecolor='#CCCCCC', 
                        linewidth=1, 
                        alpha=0.8))
        
        plt.axis('off')
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"[OK] Gorsellestirme {save_path} dosyasina kaydedildi.")
        
        plt.tight_layout()
        plt.show()

