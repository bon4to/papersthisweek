import os
import time
from mcp.server.fastmcp import FastMCP
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings
from paper_sources import search_all_sources, enrich_documents

# Load OpenAI key from .env file
load_dotenv()

# Initialize the MCP server
mcp = FastMCP("ArxivRAGServer")

# Global variable to keep the vector database in memory while the server runs
vector_db = None

def get_embeddings() -> Embeddings:
    """
    Returns the configured embeddings model based on the EMBEDDING_PROVIDER environment variable.
    Options: 'openai', 'gemini', 'local'
    Default: 'local' (local model via Ollama)
    """
    provider = os.getenv("EMBEDDING_PROVIDER", "local").lower()
    
    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model="text-embedding-3-small")
    
    elif provider == "gemini":
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in .env")
            return GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=api_key
            )
        except ImportError:
            raise ImportError(
                "langchain-google-genai not installed. "
                "Install with: pip install langchain-google-genai"
            )
    
    elif provider == "local":
        try:
            from langchain_community.embeddings import OllamaEmbeddings
            model_name = os.getenv("LOCAL_EMBEDDING_MODEL", "nomic-embed-text")
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            return OllamaEmbeddings(
                model=model_name,
                base_url=base_url
            )
        except ImportError:
            raise ImportError(
                "langchain-community not installed. "
                "Install with: pip install langchain-community"
            )
        except Exception as e:
            error_msg = str(e).lower()
            if "connection" in error_msg or "refused" in error_msg or "unreachable" in error_msg:
                raise ConnectionError(
                    f"Ollama is not running at {base_url}. "
                    "Start Ollama with: ollama serve\n"
                    "Ou instale: https://ollama.ai"
                )
            elif "model" in error_msg and "not found" in error_msg:
                raise ValueError(
                    f"Embedding model '{model_name}' not found in Ollama. "
                    f"Download with: ollama pull {model_name}"
                )
            raise
    
    else:
        raise ValueError(
            f"EMBEDDING_PROVIDER '{provider}' not supported. "
            "Use: 'openai', 'gemini', or 'local'"
        )

@mcp.tool()
def update_knowledge_base(
    tema: str, 
    max_papers: int = 10,
    sources: str = "arxiv,semantic_scholar"
) -> str:
    """
    Downloads recent technology papers from multiple sources, creates embeddings and saves in memory (RAG).
    Focused on tech news and technology research.
    
    Args:
        tema: Theme/keywords to search (tech-related)
        max_papers: Maximum number of papers (distributed between sources)
        sources: Sources separated by comma. Options: arxiv, semantic_scholar
                 Example: "arxiv,semantic_scholar" or just "arxiv"
    
    Use this before asking questions.
    """
    global vector_db
    print(f"📥 [SERVER] Downloading papers about: {tema}...")
    
    try:
        # Parse the sources
        source_list = [s.strip().lower() for s in sources.split(",")]
        max_per_source = max(1, max_papers // len(source_list))  # Distribute between sources
        
        print(f"🔍 [SERVER] Searching in: {', '.join([s.upper() for s in source_list])}")
        print(f"📊 [SERVER] Maximum per source: {max_per_source}")
        
        # Search in all sources
        raw_docs = search_all_sources(tema, source_list, max_per_source)
        
        if not raw_docs:
            return f"No papers found in the sources {sources} for this theme."

        # Enrich the documents
        raw_docs = enrich_documents(raw_docs)
        
        print(f"📚 [SERVER] Total papers found: {len(raw_docs)}")

        # Chunking for the RAG
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs_split = text_splitter.split_documents(raw_docs)

        # Creation of the vectors
        provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
        print(f"🧠 [SERVER] Using embeddings: {provider.upper()}")
        embeddings = get_embeddings()
        
        print(f"🧠 [SERVER] Vectorizing {len(docs_split)} fragments...")
        
        # Try to create vectors with retry for rate limits
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Create or update the FAISS database
                if vector_db is None:
                    vector_db = FAISS.from_documents(docs_split, embeddings)
                else:
                    vector_db.add_documents(docs_split)
                break
            except Exception as e:
                error_str = str(e).lower()
                
                # Specific treatment for OpenAI
                if provider == "openai":
                    try:
                        from openai import RateLimitError, APIError
                        if isinstance(e, RateLimitError):
                            if attempt < max_retries - 1:
                                wait_time = retry_delay * (2 ** attempt)
                                print(f"⚠️  [SERVER] Rate limit reached. Waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                                time.sleep(wait_time)
                                continue
                            else:
                                return f"Error: OpenAI quota exceeded. Check: https://platform.openai.com/account/billing or use EMBEDDING_PROVIDER=gemini/local"
                        elif isinstance(e, APIError) and "insufficient_quota" in error_str:
                            return f"Error: Insufficient quota. Add credits or use EMBEDDING_PROVIDER=gemini/local"
                    except ImportError:
                        pass
                
                # Generic treatment for rate limits
                if "rate limit" in error_str or "429" in error_str or "quota" in error_str:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)
                        print(f"⚠️  [SERVER] Rate limit reached. Waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                    else:
                        return f"Error: Rate limit or quota exceeded for {provider}. Details: {str(e)}"
                else:
                    if attempt < max_retries - 1:
                        print(f"⚠️  [SERVER] Error: {e}. Trying again... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay * (2 ** attempt))
                    else:
                        return f"Error creating embeddings: {str(e)}"
            
        return f"Success! {len(raw_docs)} papers were indexed in the RAG."

    except Exception as e:
        return f"Error processing papers: {str(e)}"

@mcp.tool()
def query_rag(question: str) -> str:
    """
    Query the vector database to find relevant fragments of papers.
    """
    global vector_db
    if vector_db is None:
        return "The knowledge base is empty. Use 'update_knowledge_base' first."
    
    try:
        print(f"🔍 [SERVER] Searching for similarity for: '{question}'")
        results = vector_db.similarity_search(question, k=5)
        
        contexto = ""
        for doc in results:
            contexto += f"\n---\n{doc.page_content}\n"
            
        return contexto
    except Exception as e:
        return f"Error querying RAG: {str(e)}"

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
