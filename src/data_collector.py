"""
Akademik Yayın Verilerini Toplama Modülü

Bu modül, Semantic Scholar API kullanarak akademik yayın verilerini toplar.
Toplanan veriler:
- Yayın başlıkları
- Özetler
- Yazar isimleri
- Atıf sayıları
- Yayın URL'leri
"""

import time
import ast
import re
from typing import List, Dict, Optional
import pandas as pd
import requests


class ScholarDataCollector:
    """
    Akademik yayın verilerini toplama sınıfı
    
    Semantic Scholar API kullanarak akademik yayınları arar ve toplar.
    Rate limiting ve retry mekanizması ile güvenilir veri toplama sağlar.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        delay: float = 3.0,
        timeout: float = 30.0
    ):
        """
        Args:
            api_key: Semantic Scholar API key (opsiyonel)
                     API key ile rate limit 5000 istek/5 dakika'ya çıkar
                     API key olmadan: 100 istek/5 dakika
            delay: İstekler arası bekleme süresi (saniye)
                   Rate limit'i aşmamak için minimum 3 saniye önerilir
            timeout: Her API isteği için timeout süresi (saniye)
        """
        self.api_key = api_key
        self.delay = delay
        self.timeout = timeout
        self.collected_publications = []
        self.api_base_url = "https://api.semanticscholar.org/graph/v1"
        
        print("[OK] Semantic Scholar API modu aktif")
        if api_key:
            print("[OK] API key kullanılıyor (yüksek rate limit)")
    
    def _api_request(self, endpoint: str, params: Dict = None, max_retries: int = 3) -> Optional[Dict]:
        """
        Semantic Scholar API'ye HTTP isteği gönderir
        
        Retry mekanizması ile rate limiting ve timeout hatalarını yönetir.
        
        Args:
            endpoint: API endpoint (örn: 'paper/search')
            params: İstek parametreleri
            max_retries: Maksimum retry sayısı
            
        Returns:
            API yanıtı (JSON dict) veya None (hata durumunda)
        """
        url = f"{self.api_base_url}/{endpoint}"
        headers = {
            'User-Agent': 'Academic Analysis Tool',
            'Accept': 'application/json'
        }
        
        if self.api_key:
            headers['x-api-key'] = self.api_key
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
                
                # 429 hatası (Rate Limit) - bekleyip tekrar dene
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    wait_time = min(retry_after, 120)
                    
                    if attempt < max_retries - 1:
                        print(f"  [WAIT] Rate limit asildi! {wait_time} saniye bekleniyor... (Deneme {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"  [ERROR] Rate limit hatasi: {max_retries} deneme sonrasi basarisiz")
                        return None
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"  [WAIT] Timeout! {wait_time} saniye bekleniyor... (Deneme {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"  [ERROR] Timeout hatasi: {max_retries} deneme sonrasi basarisiz")
                    return None
                    
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"  [WAIT] Hata: {e}. {wait_time} saniye bekleniyor... (Deneme {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"  [ERROR] API istegi hatasi: {e}")
                    return None
        
        return None
    
    def _parse_api_paper(self, paper_data: Dict) -> Optional[Dict]:
        """
        API'den gelen yayın verisini standart formata dönüştürür
        
        Args:
            paper_data: API'den gelen ham yayın verisi (dict)
            
        Returns:
            Standart formatta yayın verisi (dict) veya None
        """
        # Yazar isimlerini çıkar
        authors = []
        if 'authors' in paper_data:
            authors = [author.get('name', '') for author in paper_data['authors'] if author.get('name')]
        
        # Atıf sayısı
        citation_count = paper_data.get('citationCount', 0) or 0
        
        # Yayın URL'si (öncelik: DOI, sonra direkt URL)
        url = ""
        if 'externalIds' in paper_data and 'DOI' in paper_data['externalIds']:
            url = f"https://doi.org/{paper_data['externalIds']['DOI']}"
        elif 'url' in paper_data:
            url = paper_data['url']
        
        return {
            'title': paper_data.get('title', ''),
            'abstract': paper_data.get('abstract', ''),
            'authors': authors,
            'citation_count': citation_count,
            'pub_url': url
        }
    
    def search_publications(
        self, 
        query: str, 
        max_results: int = 100
    ) -> List[Dict]:
        """
        Semantic Scholar API ile yayın arama
        
        Belirli bir sorgu ile akademik yayınları arar ve toplar.
        Pagination ile birden fazla sayfa sonuçlarını toplar.
        
        Args:
            query: Arama sorgusu (örn: "machine learning")
            max_results: Maksimum toplanacak yayın sayısı
            
        Returns:
            Yayın bilgilerini içeren liste
        """
        publications = []
        offset = 0
        limit = min(100, max_results)  # API limit: maksimum 100 sonuç/istek
        
        print(f"  🔍 Semantic Scholar API'de aranıyor: '{query}'")
        
        # Pagination ile tüm sonuçları topla
        while len(publications) < max_results:
            # API istek parametreleri
            params = {
                'query': query,
                'limit': limit,
                'offset': offset,
                'fields': 'title,abstract,authors,citationCount,externalIds,url'
            }
            
            # API isteği gönder
            response_data = self._api_request('paper/search', params)
            
            # Hata kontrolü
            if not response_data or 'data' not in response_data:
                break
            
            papers = response_data.get('data', [])
            if not papers:
                break
            
            # Her yayını parse et ve listeye ekle
            for paper in papers:
                if len(publications) >= max_results:
                    break
                
                pub_data = self._parse_api_paper(paper)
                if pub_data and pub_data['title']:
                    publications.append(pub_data)
                    print(f"  [OK] {len(publications)}/{max_results} yayın toplandı: {pub_data['title'][:50]}...", end='\r')
            
            # Rate limiting için bekle (minimum 3 saniye)
            time.sleep(max(self.delay, 3.0))
            
            # Sonraki sayfa için offset artır
            offset += limit
            
            # Eğer daha az sonuç geldiyse, daha fazla sayfa yok demektir
            if len(papers) < limit:
                break
        
        print(f"\n  [OK] '{query}' sorgusu tamamlandı: {len(publications)} yayın toplandı")
        return publications
    
    def collect_multiple_queries(
        self, 
        queries: List[str], 
        max_results_per_query: int = 50
    ) -> pd.DataFrame:
        """
        Birden fazla sorgu ile veri toplar
        
        Her sorgu için ayrı ayrı arama yapar ve sonuçları birleştirir.
        Sorgular arası rate limiting için bekleme süresi ekler.
        
        Args:
            queries: Arama sorguları listesi
            max_results_per_query: Her sorgu için maksimum sonuç sayısı
            
        Returns:
            Tüm sorgulardan toplanan yayınların DataFrame'i
        """
        all_publications = []
        
        print(f"\n[INFO] Toplam {len(queries)} sorgu işlenecek")
        print(f"[INFO] Her istek icin timeout: {self.timeout} saniye")
        print(f"[INFO] Her sorgu icin maksimum {max_results_per_query} sonuc\n")
        
        # Her sorgu için arama yap
        for idx, query in enumerate(queries, 1):
            print(f"\n{'='*60}")
            print(f"Sorgu {idx}/{len(queries)}: '{query}'")
            print(f"{'='*60}")
            
            try:
                publications = self.search_publications(query, max_results_per_query)
                all_publications.extend(publications)
                print(f"[OK] Sorgu {idx} tamamlandı: {len(publications)} yayın toplandı")
            except Exception as e:
                print(f"[ERROR] Sorgu {idx} basarisiz: {e}")
                continue
            
            # Sorgular arası bekleme (API rate limit: 100 istek/5 dakika)
            if idx < len(queries):
                wait_time = 10  # Rate limit'i aşmamak için 10 saniye bekle
                print(f"[WAIT] Sonraki sorgu icin {wait_time} saniye bekleniyor...")
                time.sleep(wait_time)
        
        print(f"\n{'='*60}")
        print(f"[INFO] Toplam {len(all_publications)} yayin toplandi")
        print(f"{'='*60}\n")
        
        # DataFrame'e dönüştür
        if len(all_publications) > 0:
            df = pd.DataFrame(all_publications)
            self.collected_publications = all_publications
        else:
            print("[WARNING] Hic yayin toplanamadi! Bos DataFrame olusturuluyor...")
            df = pd.DataFrame()
        
        return df
    
    def save_to_csv(self, df: pd.DataFrame, filename: str = "publications.csv"):
        """
        Verileri CSV dosyasına kaydeder
        
        Args:
            df: Kaydedilecek DataFrame
            filename: Dosya yolu
        """
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"[OK] {len(df)} yayin {filename} dosyasina kaydedildi.")
    
    def load_from_csv(self, filename: str = "publications.csv") -> pd.DataFrame:
        """
        CSV dosyasından veri yükler
        
        CSV'den okunan verileri parse eder:
        - authors kolonu string'den listeye dönüştürülür
        - citation_count numeric'e dönüştürülür
        
        Args:
            filename: Yüklenecek CSV dosyası yolu
            
        Returns:
            Yüklenen verilerin DataFrame'i
        """
        import os
        
        # Dosya varlık kontrolü
        if not os.path.exists(filename):
            print(f"[WARNING] Dosya bulunamadi: {filename}")
            return pd.DataFrame()
        
        if os.path.getsize(filename) == 0:
            print(f"[WARNING] Dosya bos: {filename}")
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(filename)
            
            if df.empty or len(df) == 0:
                print(f"[WARNING] CSV dosyasi bos: {filename}")
                self.collected_publications = []
                return pd.DataFrame()
            
            # authors kolonunu string'den listeye dönüştür
            # CSV'ye kaydedilirken liste string'e dönüşmüş olabilir
            if 'authors' in df.columns:
                def parse_authors(author_str):
                    """Yazar string'ini listeye dönüştürür"""
                    if pd.isna(author_str) or author_str == '':
                        return []
                    if isinstance(author_str, list):
                        return author_str
                    if isinstance(author_str, str):
                        try:
                            # Python list formatını parse et: "['Author1', 'Author2']"
                            parsed = ast.literal_eval(author_str)
                            if isinstance(parsed, list):
                                return parsed
                        except (ValueError, SyntaxError):
                            # Manuel parse: köşeli parantez içindeki isimleri çıkar
                            author_str = author_str.strip()
                            if author_str.startswith('[') and author_str.endswith(']'):
                                author_str = author_str[1:-1]
                                authors = re.findall(r"['\"]([^'\"]+)['\"]", author_str)
                                return [a.strip() for a in authors if a.strip()]
                            # Virgülle ayrılmış string ise
                            return [a.strip() for a in author_str.split(',') if a.strip()]
                    return []
                
                df['authors'] = df['authors'].apply(parse_authors)
            
            # citation_count'u numeric'e dönüştür
            if 'citation_count' in df.columns:
                df['citation_count'] = pd.to_numeric(df['citation_count'], errors='coerce').fillna(0).astype(int)
            
            self.collected_publications = df.to_dict('records')
            print(f"[OK] {len(df)} yayin CSV'den yuklendi")
            return df
            
        except pd.errors.EmptyDataError:
            print(f"[WARNING] CSV dosyasi bos veya gecersiz: {filename}")
            return pd.DataFrame()
        except Exception as e:
            print(f"[ERROR] CSV yukleme hatasi: {e}")
            return pd.DataFrame()
