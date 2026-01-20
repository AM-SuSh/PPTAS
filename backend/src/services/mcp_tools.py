"""
MCP (Model Context Protocol) 工具集成
支持维基百科、Arxiv、Google Scholar 等外部知识源
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document
import xml.etree.ElementTree as ET


@dataclass
class SearchResult:
    """搜索结果"""
    title: str
    content: str
    url: str
    source: str
    metadata: Dict[str, Any]


class WikipediaMCP:
    """维基百科 MCP 工具"""
    
    def __init__(self, language: str = "zh"):
        self.language = language
        self.api_url = f"https://{language}.wikipedia.org/w/api.php"
        self.headers = {
            "User-Agent": "PPTAS-Bot/1.0 (https://github.com/user/pptas)"
        }
    
    def search(self, query: str, limit: int = 3) -> List[Document]:
        """搜索维基百科"""
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "srlimit": limit
        }
        
        try:
            response = requests.get(self.api_url, params=params, timeout=10, headers=self.headers)
            response.raise_for_status()  # 检查 HTTP 状态
            
            # 检查响应是否为空
            if not response.text:
                print(f"Wikipedia search error: Empty response for query '{query}'")
                return []
            
            data = response.json()
            
            documents = []
            for item in data.get("query", {}).get("search", []):
                # 获取页面内容
                content = self._get_page_content(item["title"])
                if content:
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "source": "Wikipedia",
                            "title": item["title"],
                            "url": f"https://{self.language}.wikipedia.org/wiki/{item['title'].replace(' ', '_')}"
                        }
                    ))
            
            return documents
        except Exception as e:
            print(f"Wikipedia search error: {type(e).__name__}: {e}")
            return []
    
    def _get_page_content(self, title: str) -> Optional[str]:
        """获取页面内容摘要"""
        params = {
            "action": "query",
            "format": "json",
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "titles": title
        }
        
        try:
            response = requests.get(self.api_url, params=params, timeout=10, headers=self.headers)
            response.raise_for_status()
            
            if not response.text:
                return None
            
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            
            for page in pages.values():
                content = page.get("extract", "")
                if content:
                    return content[:1000]  # 限制长度
            
            return None
        except Exception as e:
            print(f"Get Wikipedia page content error: {type(e).__name__}: {e}")
            return None


class ArxivMCP:
    """Arxiv MCP 工具"""
    
    def __init__(self):
        self.api_url = "http://export.arxiv.org/api/query"
    
    def search(self, query: str, max_results: int = 3) -> List[Document]:
        """搜索 Arxiv 论文"""
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }
        
        try:
            response = requests.get(self.api_url, params=params, timeout=15)
            root = ET.fromstring(response.content)
            
            documents = []
            for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
                title = entry.find("{http://www.w3.org/2005/Atom}title").text.strip()
                summary = entry.find("{http://www.w3.org/2005/Atom}summary").text.strip()
                link = entry.find("{http://www.w3.org/2005/Atom}id").text.strip()
                
                # 获取作者
                authors = []
                for author in entry.findall("{http://www.w3.org/2005/Atom}author"):
                    name = author.find("{http://www.w3.org/2005/Atom}name").text
                    authors.append(name)
                
                documents.append(Document(
                    page_content=f"{title}\n\n{summary[:800]}",
                    metadata={
                        "source": "Arxiv",
                        "title": title,
                        "authors": ", ".join(authors),
                        "url": link
                    }
                ))
            
            return documents
        except Exception as e:
            print(f"Arxiv search error: {e}")
            return []


class GoogleScholarMCP:
    """Google Scholar MCP 工具（简化版）"""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    def search(self, query: str, num_results: int = 3) -> List[Document]:
        """搜索 Google Scholar
        注意：这是简化版，生产环境建议使用 SerpAPI 等服务
        """
        url = f"https://scholar.google.com/scholar?q={query}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            documents = []
            results = soup.find_all('div', class_='gs_ri')[:num_results]
            
            for result in results:
                title_elem = result.find('h3', class_='gs_rt')
                title = title_elem.get_text() if title_elem else "Unknown"
                
                snippet_elem = result.find('div', class_='gs_rs')
                snippet = snippet_elem.get_text() if snippet_elem else ""
                
                link_elem = title_elem.find('a') if title_elem else None
                link = link_elem['href'] if link_elem else ""
                
                documents.append(Document(
                    page_content=f"{title}\n\n{snippet[:500]}",
                    metadata={
                        "source": "Google Scholar",
                        "title": title,
                        "url": link
                    }
                ))
            
            return documents
        except Exception as e:
            print(f"Google Scholar search error: {e}")
            return []


class BaiduBaikeMCP:
    """百度百科 MCP 工具"""
    
    def __init__(self):
        self.base_url = "https://baike.baidu.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    def search(self, query: str) -> List[Document]:
        """搜索百度百科"""
        search_url = f"{self.base_url}/search?word={query}"
        
        try:
            response = requests.get(search_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 获取第一个搜索结果
            first_result = soup.find('dd', class_='search-list')
            if not first_result:
                return []
            
            link = first_result.find('a')['href']
            full_url = self.base_url + link
            
            # 获取词条内容
            content_response = requests.get(full_url, headers=self.headers, timeout=10)
            content_soup = BeautifulSoup(content_response.text, 'html.parser')
            
            # 提取摘要
            summary = content_soup.find('div', class_='lemma-summary')
            if summary:
                content = summary.get_text().strip()[:1000]
                
                return [Document(
                    page_content=content,
                    metadata={
                        "source": "Baidu Baike",
                        "title": query,
                        "url": full_url
                    }
                )]
            
            return []
        except Exception as e:
            print(f"Baidu Baike search error: {e}")
            return []


class MCPRouter:
    """MCP 工具路由器 - 智能选择最佳工具"""
    
    def __init__(self):
        self.tools = {
            "wikipedia": WikipediaMCP(),
            "arxiv": ArxivMCP(),
            "scholar": GoogleScholarMCP(),
            "baike": BaiduBaikeMCP()
        }
        # 只启用稳定的源，禁用容易出错的网络源
        self.enabled_sources = ["arxiv"]  
    
    def search(self, query: str, preferred_sources: List[str] = None) -> List[Document]:
        """智能搜索
        
        Args:
            query: 搜索查询
            preferred_sources: 优先使用的源，如 ["arxiv", "wikipedia"]
        """
        all_documents = []
        
        # 如果指定了优先源，检查是否启用
        if preferred_sources:
            for source in preferred_sources:
                if source not in self.enabled_sources:
                    print(f"Source {source} is disabled (network unstable), skipping...")
                    continue
                if source in self.tools:
                    try:
                        docs = self.tools[source].search(query)
                        all_documents.extend(docs)
                    except Exception as e:
                        print(f"Error searching {source}: {e}")
                        continue
        else:
            # 自动选择：优先使用 Arxiv（更稳定）
            try:
                all_documents.extend(self.tools["arxiv"].search(query, max_results=3))
            except Exception as e:
                print(f"Arxiv search failed: {e}")
        
        # 如果没有结果，返回一个占位符
        if not all_documents:
            print(f"No results found for query: {query}")
            all_documents = [Document(
                page_content=f"未找到关于 '{query}' 的学术资源。这可能是因为网络连接问题或搜索词不匹配。",
                metadata={
                    "source": "Local",
                    "title": query,
                    "url": ""
                }
            )]
        
        # 去重
        seen_urls = set()
        unique_docs = []
        for doc in all_documents:
            url = doc.metadata.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_docs.append(doc)
            elif not url:
                # 允许本地占位符文档
                unique_docs.append(doc)
        
        return unique_docs[:5]  # 限制结果数量
    
    def _is_academic_query(self, query: str) -> bool:
        """判断是否为学术查询"""
        academic_keywords = [
            "algorithm", "model", "neural", "learning", "theory",
            "算法", "模型", "神经", "学习", "理论", "公式", "证明"
        ]
        return any(keyword in query.lower() for keyword in academic_keywords)
