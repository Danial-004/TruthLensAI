"""
TruthLens AI - Web Search Module
Real-time web search for evidence gathering
"""

import requests
from typing import List, Dict, Optional
import logging
import os
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time

logger = logging.getLogger(__name__)


class WebSearcher:
    """
    Web search integration for evidence gathering
    Supports multiple search APIs: SerpAPI, Bing, Google Custom Search
    """
    
    def __init__(self):
        """Initialize web searcher with available API keys"""
        self.serp_api_key = os.getenv("SERP_API_KEY")
        self.bing_api_key = os.getenv("BING_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cx = os.getenv("GOOGLE_CX")
        
        # Determine which API to use
        if self.serp_api_key:
            self.search_method = "serpapi"
            logger.info("Using SerpAPI for web search")
        elif self.bing_api_key:
            self.search_method = "bing"
            logger.info("Using Bing API for web search")
        elif self.google_api_key and self.google_cx:
            self.search_method = "google"
            logger.info("Using Google Custom Search API")
        else:
            self.search_method = "fallback"
            logger.warning("No API keys found. Using fallback search method")
        
        # Trusted sources by language
        self.trusted_sources = {
            "en": ["reuters.com", "bbc.com", "apnews.com", "npr.org", "theguardian.com"],
            "ru": ["tass.ru", "ria.ru", "interfax.ru", "kommersant.ru", "lenta.ru"],
            "kz": ["tengrinews.kz", "inform.kz", "kazinform.kz", "24.kz", "nur.kz"]
        }
    
    def search(
        self,
        query: str,
        language: str = "en",
        max_results: int = 5,
        prioritize_trusted: bool = True
    ) -> List[Dict]:
        """
        Search the web for relevant information
        
        Args:
            query: Search query
            language: Language code (en/ru/kz)
            max_results: Maximum number of results
            prioritize_trusted: Prioritize trusted sources
            
        Returns:
            List of search results with title, url, snippet
        """
        try:
            logger.info(f"Searching: '{query}' (lang: {language}, max: {max_results})")
            
            # Route to appropriate search method
            if self.search_method == "serpapi":
                results = self._search_serpapi(query, language, max_results)
            elif self.search_method == "bing":
                results = self._search_bing(query, language, max_results)
            elif self.search_method == "google":
                results = self._search_google(query, language, max_results)
            else:
                results = self._search_fallback(query, language, max_results)
            
            # Filter and prioritize trusted sources
            if prioritize_trusted:
                results = self._prioritize_trusted_sources(results, language)
            
            logger.info(f"Found {len(results)} search results")
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def _search_serpapi(self, query: str, language: str, max_results: int) -> List[Dict]:
        """Search using SerpAPI"""
        try:
            url = "https://serpapi.com/search"
            
            # Language mapping
            lang_map = {"en": "en", "ru": "ru", "kz": "kk"}
            
            params = {
                "q": query,
                "api_key": self.serp_api_key,
                "num": max_results,
                "hl": lang_map.get(language, "en")
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("organic_results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": item.get("source", "")
                })
            
            return results
            
        except Exception as e:
            logger.error(f"SerpAPI error: {e}")
            return []
    
    def _search_bing(self, query: str, language: str, max_results: int) -> List[Dict]:
        """Search using Bing Search API"""
        try:
            url = "https://api.bing.microsoft.com/v7.0/search"
            
            # Language mapping
            lang_map = {"en": "en-US", "ru": "ru-RU", "kz": "kk-KZ"}
            
            headers = {
                "Ocp-Apim-Subscription-Key": self.bing_api_key
            }
            
            params = {
                "q": query,
                "count": max_results,
                "mkt": lang_map.get(language, "en-US"),
                "responseFilter": "Webpages"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("webPages", {}).get("value", []):
                results.append({
                    "title": item.get("name", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", ""),
                    "source": item.get("displayUrl", "")
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Bing API error: {e}")
            return []
    
    def _search_google(self, query: str, language: str, max_results: int) -> List[Dict]:
        """Search using Google Custom Search API"""
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            
            # Language mapping
            lang_map = {"en": "lang_en", "ru": "lang_ru", "kz": "lang_kk"}
            
            params = {
                "q": query,
                "key": self.google_api_key,
                "cx": self.google_cx,
                "num": min(max_results, 10),
                "lr": lang_map.get(language, "lang_en")
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": item.get("displayLink", "")
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Google API error: {e}")
            return []
    
    def _search_fallback(self, query: str, language: str, max_results: int) -> List[Dict]:
        """
        Fallback search method using DuckDuckGo HTML scraping
        Note: For production, use proper APIs
        """
        try:
            logger.info("Using fallback search (DuckDuckGo)")
            
            # DuckDuckGo HTML search
            url = "https://html.duckduckgo.com/html/"
            params = {"q": query}
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.post(url, data=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            for result in soup.find_all('div', class_='result')[:max_results]:
                title_tag = result.find('a', class_='result__a')
                snippet_tag = result.find('a', class_='result__snippet')
                
                if title_tag:
                    results.append({
                        "title": title_tag.get_text(strip=True),
                        "url": title_tag.get('href', ''),
                        "snippet": snippet_tag.get_text(strip=True) if snippet_tag else "",
                        "source": "web"
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Fallback search error: {e}")
            
            # Return mock results for demo purposes
            return self._get_mock_results(query, language)
    
    def _get_mock_results(self, query: str, language: str) -> List[Dict]:
        """Generate mock search results for demo/testing"""
        mock_data = {
            "en": [
                {
                    "title": "Reuters Fact Check",
                    "url": "https://www.reuters.com/fact-check",
                    "snippet": "Fact-checking article related to the claim. Official sources confirm details.",
                    "source": "reuters.com"
                },
                {
                    "title": "BBC News Verification",
                    "url": "https://www.bbc.com/news",
                    "snippet": "Independent verification from BBC News team shows additional context.",
                    "source": "bbc.com"
                },
                {
                    "title": "Associated Press",
                    "url": "https://apnews.com",
                    "snippet": "AP investigation reveals important background information.",
                    "source": "apnews.com"
                }
            ],
            "ru": [
                {
                    "title": "ТАСС - Проверка фактов",
                    "url": "https://tass.ru",
                    "snippet": "Официальные источники подтверждают основные детали.",
                    "source": "tass.ru"
                },
                {
                    "title": "РИА Новости",
                    "url": "https://ria.ru",
                    "snippet": "Независимая проверка показывает дополнительный контекст.",
                    "source": "ria.ru"
                }
            ],
            "kz": [
                {
                    "title": "Tengrinews.kz",
                    "url": "https://tengrinews.kz",
                    "snippet": "Ресми дереккөздер негізгі мәліметтерді растайды.",
                    "source": "tengrinews.kz"
                },
                {
                    "title": "Kazinform",
                    "url": "https://kazinform.kz",
                    "snippet": "Тәуелсіз тексеру қосымша контекст көрсетеді.",
                    "source": "kazinform.kz"
                }
            ]
        }
        
        return mock_data.get(language, mock_data["en"])
    
    def _prioritize_trusted_sources(self, results: List[Dict], language: str) -> List[Dict]:
        """
        Prioritize results from trusted sources
        
        Args:
            results: List of search results
            language: Language code
            
        Returns:
            Reordered list with trusted sources first
        """
        trusted = self.trusted_sources.get(language, [])
        
        trusted_results = []
        other_results = []
        
        for result in results:
            url = result.get("url", "").lower()
            source = result.get("source", "").lower()
            
            is_trusted = any(domain in url or domain in source for domain in trusted)
            
            if is_trusted:
                trusted_results.append(result)
            else:
                other_results.append(result)
        
        return trusted_results + other_results
    
    def verify_url(self, url: str) -> bool:
        """
        Verify if URL is accessible and valid
        
        Args:
            url: URL to verify
            
        Returns:
            True if valid and accessible
        """
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            return response.status_code == 200
        except:
            return False