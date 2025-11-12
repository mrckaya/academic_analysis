"""
Veri İşleme ve Temizleme Modülü

Bu modül, toplanan ham verileri temizler, yazarları çıkarır ve
yazar istatistiklerini hesaplar.
"""

import pandas as pd
import re
import ast


class DataProcessor:
    """
    Veri işleme ve temizleme sınıfı
    
    Toplanan ham verileri temizler, yazarları çıkarır ve
    yazar bazlı istatistikler hesaplar.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Args:
            df: Yayın verilerini içeren DataFrame
                Gerekli kolonlar: title, abstract, authors, citation_count
        """
        self.df = df.copy()
        self.processed_df = None
    
    def clean_data(self) -> pd.DataFrame:
        """
        Verileri temizler ve standartlaştırır
        
        Yapılan işlemler:
        - Eksik değerleri doldurur
        - Yazar listelerini temizler
        - Boş başlıklı yayınları kaldırır
        - Duplicate yayınları kaldırır
        
        Returns:
            Temizlenmiş DataFrame
        """
        df = self.df.copy()
        
        # Boş DataFrame kontrolü
        if df.empty or len(df) == 0:
            print("[WARNING] Uyari: Bos veri seti! Temizleme atlaniyor.")
            self.processed_df = df
            return df
        
        # Gerekli kolonları kontrol et
        required_columns = ['title', 'abstract', 'citation_count', 'authors']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"[WARNING] Uyari: Eksik kolonlar: {missing_columns}. Bos veri seti donduruluyor.")
            self.processed_df = pd.DataFrame()
            return pd.DataFrame()
        
        # Eksik değerleri temizle
        df['title'] = df['title'].fillna('')
        df['abstract'] = df['abstract'].fillna('')
        df['citation_count'] = pd.to_numeric(df['citation_count'], errors='coerce').fillna(0)
        
        # Yazar listelerini temizle
        df['authors'] = df['authors'].apply(self._clean_author_list)
        
        # Boş başlıklı yayınları kaldır
        df = df[df['title'].str.strip() != '']
        
        # Duplicate'leri kaldır (başlığa göre)
        if len(df) > 0:
            df = df.drop_duplicates(subset=['title'], keep='first')
        
        self.processed_df = df
        return df
    
    def _clean_author_list(self, authors):
        """
        Yazar listesini temizler ve standart formata dönüştürür
        
        Farklı formatlardaki yazar verilerini (string, list) temiz bir listeye dönüştürür.
        
        Args:
            authors: Yazar verisi (string, list veya None)
            
        Returns:
            Temizlenmiş yazar listesi
        """
        # None veya NaN kontrolü
        if authors is None:
            return []
        
        try:
            if pd.isna(authors):
                return []
        except (TypeError, ValueError):
            pass
        
        # Boş string kontrolü
        if isinstance(authors, str) and authors.strip() == '':
            return []
        
        # Liste zaten temizlenmişse direkt döndür
        if isinstance(authors, list):
            cleaned = []
            for author in authors:
                if isinstance(author, str):
                    author = author.strip()
                    # Köşeli parantezleri ve tırnak işaretlerini temizle
                    author = re.sub(r'^[\'\"\[\]]+|[\'\"\[\]]+$', '', author).strip()
                    if author:
                        cleaned.append(author)
            return cleaned
        
        # String ise listeye dönüştür
        if isinstance(authors, str):
            author_str = authors.strip()
            # Python list formatı: "['Author1', 'Author2']"
            if author_str.startswith('[') and author_str.endswith(']'):
                try:
                    parsed = ast.literal_eval(author_str)
                    if isinstance(parsed, list):
                        return [a.strip() for a in parsed if isinstance(a, str) and a.strip()]
                except (ValueError, SyntaxError):
                    # Manuel parse: köşeli parantez içindeki isimleri çıkar
                    author_str = author_str[1:-1]
                    authors_list = re.findall(r"['\"]([^'\"]+)['\"]", author_str)
                    return [a.strip() for a in authors_list if a.strip()]
            # Virgülle ayrılmış string
            authors_list = [a.strip() for a in author_str.split(',') if a.strip()]
            cleaned = []
            for a in authors_list:
                a = re.sub(r'^[\'\"\[\]]+|[\'\"\[\]]+$', '', a).strip()
                if a:
                    cleaned.append(a)
            return cleaned
        
        return []
    
    def extract_authors(self) -> pd.DataFrame:
        """
        Yazarları yayınlardan çıkarır
        
        Her yayındaki yazarları ayrı satırlara dönüştürür.
        Bir yazar birden fazla yayında varsa, her yayın için ayrı satır oluşturulur.
        
        Returns:
            Yazar-yayın ilişkilerini içeren DataFrame
            Kolonlar: author_name, publication_title, citation_count, abstract
        """
        if self.processed_df is None:
            self.clean_data()
        
        author_records = []
        
        # Her yayındaki yazarları çıkar
        for idx, row in self.processed_df.iterrows():
            authors = row['authors']
            if not authors or len(authors) == 0:
                continue
            
            # Her yazar için bir kayıt oluştur
            for author in authors:
                author_records.append({
                    'author_name': author,
                    'publication_title': row['title'],
                    'citation_count': row['citation_count'],
                    'abstract': row.get('abstract', '')
                })
        
        authors_df = pd.DataFrame(author_records)
        return authors_df
    
    def normalize_author_names(self, authors_df: pd.DataFrame) -> pd.DataFrame:
        """
        Yazar isimlerini normalize eder
        
        Aynı yazarın farklı yazılışlarını birleştirmek için normalizasyon yapar:
        - Küçük harfe çevirir
        - Fazla boşlukları temizler
        - author_normalized kolonu ekler
        
        Args:
            authors_df: Yazar verilerini içeren DataFrame
            
        Returns:
            Normalize edilmiş DataFrame (author_normalized kolonu eklenmiş)
        """
        # Basit normalizasyon: küçük harfe çevir, fazla boşlukları temizle
        authors_df['author_normalized'] = authors_df['author_name'].str.lower().str.strip()
        authors_df['author_normalized'] = authors_df['author_normalized'].str.replace(
            r'\s+', ' ', regex=True
        )
        
        return authors_df
    
    def calculate_author_stats(self, authors_df: pd.DataFrame) -> pd.DataFrame:
        """
        Yazarlar için istatistikler hesaplar
        
        Her yazar için:
        - Toplam yayın sayısı
        - Toplam atıf sayısı
        - Ortalama atıf/yayın
        - Yaklaşık H-index
        
        Args:
            authors_df: Yazar-yayın ilişkilerini içeren DataFrame
            
        Returns:
            Yazar istatistiklerini içeren DataFrame
            Sıralama: total_citations'a göre azalan
        """
        # Yazar bazında grupla ve istatistikleri hesapla
        grouped = authors_df.groupby('author_normalized')
        
        author_stats = pd.DataFrame({
            'publication_count': grouped['publication_title'].count(),
            'total_citations': grouped['citation_count'].sum(),
            'avg_citations_per_paper': grouped['citation_count'].mean()
        }).reset_index()
        
        # author_normalized'i author_name olarak değiştir
        author_stats.rename(columns={'author_normalized': 'author_name'}, inplace=True)
        
        # H-index benzeri metrik hesapla
        # H-index: En az h yayını, her biri en az h atıf almış
        author_stats['h_index_approx'] = author_stats.apply(
            lambda row: self._calculate_h_index_approx(
                authors_df[authors_df['author_normalized'] == row['author_name']]['citation_count']
            ),
            axis=1
        )
        
        return author_stats.sort_values('total_citations', ascending=False)
    
    def _calculate_h_index_approx(self, citations: pd.Series) -> int:
        """
        Yaklaşık H-index hesaplar
        
        H-index: Bir yazarın en az h yayını, her biri en az h atıf almış.
        
        Args:
            citations: Yazarın yayınlarının atıf sayıları (pandas Series)
            
        Returns:
            H-index değeri
        """
        if len(citations) == 0:
            return 0
        
        # Atıf sayılarını azalan sıraya göre sırala
        sorted_citations = sorted(citations, reverse=True)
        h_index = 0
        
        # H-index hesapla: i+1. yayın en az i+1 atıf almış mı?
        for i, cit in enumerate(sorted_citations):
            if cit >= i + 1:
                h_index = i + 1
            else:
                break
        
        return h_index
    
    def get_top_authors(
        self, 
        authors_df: pd.DataFrame, 
        top_n: int = 50,
        by: str = 'total_citations'
    ) -> pd.DataFrame:
        """
        En etkili yazarları döndürür
        
        Args:
            authors_df: Yazar istatistiklerini içeren DataFrame
            top_n: Döndürülecek yazar sayısı
            by: Sıralama kriteri ('total_citations', 'publication_count', 'h_index_approx')
            
        Returns:
            En etkili yazarları içeren DataFrame
        """
        # Güvenlik için duplicate'leri kaldır
        authors_df = authors_df.drop_duplicates(subset=['author_name'], keep='first')
        
        if by == 'total_citations':
            top = authors_df.nlargest(top_n, 'total_citations')
        elif by == 'publication_count':
            top = authors_df.nlargest(top_n, 'publication_count')
        elif by == 'h_index_approx':
            top = authors_df.nlargest(top_n, 'h_index_approx')
        else:
            top = authors_df.nlargest(top_n, 'total_citations')
        
        return top

