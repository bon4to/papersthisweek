"""
Módulo para buscar papers e tech news de fontes acadêmicas.
Focado em tecnologia: ArXiv, Semantic Scholar
"""
import os
from typing import List
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

def search_arxiv(query: str, max_results: int = 10) -> List[Document]:
    """Busca papers no ArXiv."""
    try:
        from langchain_community.document_loaders import ArxivLoader
        
        loader = ArxivLoader(
            query=query,
            load_max_docs=max_results,
            sort_by="submittedDate",
            sort_order="descending"
        )
        docs = loader.load()
        
        # Enriquece com metadata
        for doc in docs:
            doc.metadata["source"] = "arxiv"
            doc.metadata["source_name"] = "ArXiv"
            if not doc.metadata.get("Entry ID"):
                doc.metadata["url"] = doc.metadata.get("Entry ID", "")
            else:
                doc.metadata["url"] = doc.metadata["Entry ID"]
        
        return docs
    except Exception as e:
        print(f"⚠️  Erro ao buscar ArXiv: {e}")
        return []


def search_semantic_scholar(query: str, max_results: int = 10) -> List[Document]:
    """Busca papers no Semantic Scholar."""
    try:
        import requests
        
        api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        
        params = {
            "query": query,
            "limit": min(max_results, 100),  # API limita a 100
            "fields": "title,authors,year,abstract,url,paperId"
        }
        
        headers = {}
        if api_key:
            headers["x-api-key"] = api_key
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
        
        data = response.json()
        docs = []
        
        if "data" in data:
            for item in data["data"][:max_results]:
                title = item.get("title", "")
                authors = ", ".join([a.get("name", "") for a in item.get("authors", [])])
                year = item.get("year", "")
                abstract = item.get("abstract", "")
                paper_id = item.get("paperId", "")
                url = item.get("url", f"https://www.semanticscholar.org/paper/{paper_id}" if paper_id else "")
                
                content = f"TÍTULO: {title}\nAUTORES: {authors}\nANO: {year}\n\nRESUMO: {abstract}"
                
                doc = Document(
                    page_content=content,
                    metadata={
                        "Title": title,
                        "Authors": authors,
                        "Published": str(year) if year else "",
                        "source": "semantic_scholar",
                        "source_name": "Semantic Scholar",
                        "url": url,
                        "paperId": paper_id
                    }
                )
                docs.append(doc)
        
        return docs
    except Exception as e:
        print(f"⚠️  Erro ao buscar Semantic Scholar: {e}")
        return []

def search_all_sources(query: str, sources: List[str], max_per_source: int = 5) -> List[Document]:
    """
    Busca papers de tecnologia em múltiplas fontes.
    
    Args:
        query: Termo de busca (tech-related)
        sources: Lista de fontes ('arxiv', 'semantic_scholar')
        max_per_source: Máximo de papers por fonte
    
    Returns:
        Lista de documentos de todas as fontes
    """
    all_docs = []
    source_functions = {
        "arxiv": search_arxiv,
        "semantic_scholar": search_semantic_scholar
    }
    
    for source in sources:
        if source.lower() in source_functions:
            print(f"🔍 Buscando em {source_functions[source.lower()].__name__.replace('search_', '').upper()}...")
            docs = source_functions[source.lower()](query, max_per_source)
            all_docs.extend(docs)
            print(f"   ✅ Encontrados {len(docs)} papers")
        else:
            print(f"⚠️  Fonte desconhecida: {source} (suportado: arxiv, semantic_scholar)")
    
    return all_docs

def enrich_documents(docs: List[Document]) -> List[Document]:
    """ Enriquece documentos com informações padronizadas."""
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        source_name = doc.metadata.get("source_name", source.upper())
        
        # Padroniza o formato do conteúdo
        title = doc.metadata.get("Title", "")
        date = doc.metadata.get("Published", "")
        url = doc.metadata.get("url", "")
        
        # Enriquece o conteúdo
        doc.page_content = (
            f"FONTE: {source_name}\n"
            f"TÍTULO: {title}\n"
            f"DATA: {date}\n"
            f"LINK: {url}\n"
            f"RESUMO: {doc.page_content}"
        )
    
    return docs

