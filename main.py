import asyncio
import os
import sys
from dotenv import load_dotenv

# Client MCP libraries
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# AI libraries to generate the final ranking
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel

load_dotenv()

def get_llm() -> BaseChatModel:
    """
    Returns the configured LLM based on the LLM_PROVIDER environment variable.
    Options: 'openai', 'gemini', 'deepseek-local'
    Default: 'deepseek-local' (local model via Ollama)
    """
    provider = os.getenv("LLM_PROVIDER", "deepseek-local").lower()
    
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        from openai import RateLimitError, APIError
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            max_retries=3,
            temperature=0.7
        )
    
    elif provider == "gemini":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY não encontrada no .env")
            # Try different model name formats
            # Some environments may need different names
            model_name = os.getenv("GEMINI_MODEL", "gemini-pro")
            
            # If the default model fails, try alternatives
            # Valid models: gemini-pro, gemini-1.0-pro, gemini-1.5-flash, gemini-1.5-pro
            return ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=0.7,
                # Try using v1 instead of v1beta if available
                convert_system_message_to_human=True
            )
        except ImportError:
            raise ImportError(
                "langchain-google-genai not installed. "
                "Install with: pip install langchain-google-genai"
            )
    
    elif provider == "deepseek-local":
        try:
            from langchain_ollama import ChatOllama
            # DeepSeek via Ollama (requires Ollama installed and model downloaded)
            model_name = os.getenv("DEEPSEEK_MODEL", "deepseek-r1:7b")
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            return ChatOllama(
                model=model_name,
                base_url=base_url,
                temperature=0.7
            )
        except ImportError:
            raise ImportError(
                "langchain-ollama not installed. "
                "Install with: pip install langchain-ollama"
            )
        except Exception as e:
            error_msg = str(e).lower()
            if "connection" in error_msg or "refused" in error_msg or "unreachable" in error_msg:
                raise ConnectionError(
                    f"Ollama is not running at {base_url}. "
                    "Start Ollama with: ollama serve\n"
                    "Or install: https://ollama.ai"
                )
            elif "model" in error_msg and "not found" in error_msg:
                raise ValueError(
                    f"Model '{model_name}' not found in Ollama. "
                    f"Download with: ollama pull {model_name}"
                )
            raise
    
    else:
        raise ValueError(
            f"LLM_PROVIDER '{provider}' not supported. "
            "Use: 'openai', 'gemini', or 'deepseek-local'"
        )

# Configuration of the LLM (The Judge)
llm = get_llm()

async def run_agent():
    # 1. Configure the connection to the local server
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(script_dir, "mcp_server.py")
    server_params = StdioServerParameters(
        command=sys.executable, # Use the same python that is running this script
        args=[server_script], # The server file
        env=os.environ
    )

    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    print(f"🔌 Connecting to the MCP server...")
    print(f"🤖 Using LLM Provider: {provider.upper()}")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List of available tools to confirm
            tools = await session.list_tools()
            print(f"🛠️ Found tools: {[t.name for t in tools.tools]}")
            
            # --- AGENT FLOW ---
            
            # Default topic: Tech News (can be configured via env)
            TEMA = os.getenv("TECH_NEWS_TOPIC", "artificial intelligence machine learning")
            
            # Step 1: The Agent sends the Server to ingest the data (RAG Ingest)
            # Search in tech sources: ArXiv, Semantic Scholar
            sources = os.getenv("PAPER_SOURCES", "arxiv,semantic_scholar")
            max_papers = int(os.getenv("MAX_PAPERS", "15"))
            
            print(f"\n🤖 AGENT: Searching tech news about '{TEMA}'...")
            print(f"📚 Sources: {sources}")
            resultado_ingestao = await session.call_tool(
                "update_knowledge_base",
                arguments={
                    "tema": TEMA, 
                    "max_papers": max_papers,
                    "sources": sources
                }
            )
            print(f"📡 SERVER RESPONSE: {resultado_ingestao.content[0].text}")

            # Passo 2: O Agente consulta o RAG para pegar os melhores trechos
            print("\n🤖 AGENT: Consulting the vector database to find innovations in tech...")
            resultado_busca = await session.call_tool(
                "query_rag",
                arguments={"pergunta": "Which papers or research present significant technological innovations, performance improvements, or recent advances in AI, machine learning, or computing?"}
            )
            contexto_rag = resultado_busca.content[0].text
            
            # Step 3: The Agent uses its local LLM to rank based on the received context
            print("\n🤖 AGENTE: Gerando Ranking Final de Tech News...")
            
            prompt = ChatPromptTemplate.from_template("""
            You are a tech news editor. Based ONLY on the context below (retrieved via RAG of academic papers),
            create a Top 5 Ranking of the most relevant and impactful research/discoveries in technology. Do not humanize the output (avoid greetings, etc.).
            
            Focus on:
            - Significant technological innovations
            - Performance improvements
            - Recent advances in AI, ML, computing
            - Potential impact on industry
            
            RAG CONTEXT:
            {contexto}
            
            OUTPUT FORMAT:
            1. [Research Title] (Score 0.0-5.0)
               - Innovation: [What is new/important about this research]
               - Impact: [Why this is important for tech]
               - Link: [Paper link]
               - Source: [Source of the paper]
            """)
            
            chain = prompt | llm
            
            # Invoke with retry and error handling
            max_retries = 3
            retry_delay = 2
            provider = os.getenv("LLM_PROVIDER", "openai").lower()
            
            for attempt in range(max_retries):
                try:
                    resposta_final = chain.invoke({"contexto": contexto_rag})
                    break
                except Exception as e:
                    error_str = str(e).lower()
                    
                    # Tratamento específico para OpenAI
                    if provider == "openai":
                        try:
                            from openai import RateLimitError, APIError
                            if isinstance(e, RateLimitError):
                                if attempt < max_retries - 1:
                                    wait_time = retry_delay * (2 ** attempt)
                                    print(f"⚠️  Rate limit reached. Waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                                    await asyncio.sleep(wait_time)
                                    continue
                                else:
                                    print("\n❌ ERROR: OpenAI quota exceeded or persistent rate limit.")
                                    print("💡 SOLUÇÕES:")
                                    print("   1. Check your account: https://platform.openai.com/account/billing")
                                    print("   2. Wait a few minutes and try again")
                                    print("   3. Use LLM_PROVIDER=gemini or LLM_PROVIDER=deepseek-local in .env")
                                    raise
                            elif isinstance(e, APIError) and "insufficient_quota" in error_str:
                                print("\n❌ ERROR: Insufficient quota in OpenAI account.")
                                print("💡 SOLUÇÕES:")
                                print("   1. Check your plan: https://platform.openai.com/account/billing")
                                print("   2. Add credits to your account")
                                print("   3. Use LLM_PROVIDER=gemini or LLM_PROVIDER=deepseek-local in .env")
                                raise
                        except ImportError:
                            pass
                    
                    # Tratamento específico para Gemini
                    if provider == "gemini":
                        if "not found" in error_str or "404" in error_str:
                            current_model = os.getenv('GEMINI_MODEL', 'gemini-pro')
                            print(f"\n❌ ERROR: Gemini model not found: {current_model}")
                            print("💡 Try using one of these models in .env:")
                            print("   - GEMINI_MODEL=gemini-pro (most compatible)")
                            print("   - GEMINI_MODEL=gemini-1.0-pro")
                            print("   - GEMINI_MODEL=gemini-1.5-flash")
                            print("   - GEMINI_MODEL=gemini-1.5-pro")
                            print("\n   Or use LLM_PROVIDER=deepseek-local for local model")
                            raise
                        elif "api key" in error_str or "authentication" in error_str:
                            print("\n❌ ERROR: Authentication problem with Google API")
                            print("💡 Check if GOOGLE_API_KEY is correct in .env")
                            raise
                        elif "quota" in error_str or "429" in error_str:
                            print("\n❌ ERROR: Gemini quota exceeded")
                            print("💡 SOLUÇÕES:")
                            print("   1. Check your usage: https://ai.dev/usage?tab=rate-limit")
                            print("   2. Wait a few minutes")
                            print("   3. Use LLM_PROVIDER=deepseek-local for local model")
                            raise
                    
                    # Tratamento genérico para rate limits
                    if "rate limit" in error_str or "429" in error_str or "quota" in error_str:
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (2 ** attempt)
                            print(f"⚠️  Rate limit reached. Waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(wait_time)
                        else:
                            print(f"\n❌ ERROR: Rate limit or quota exceeded for {provider}")
                            print(f"💡 Details: {e}")
                            raise
                    else:
                        # Outros erros - tenta novar ou falha
                        if attempt < max_retries - 1:
                            print(f"⚠️  ERROR: {e}. Trying again... (attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(retry_delay * (2 ** attempt))
                        else:
                            print(f"\n❌ ERROR: Error generating ranking: {e}")
                            raise
            
            print("\n" + "="*50)
            print("🏆 TOP 5 PAPERS/NEWS OF THE WEEK (GENERATED WITH MCP + RAG)")
            print("="*50)
            print(resposta_final.content)
            
            # Send via Telegram if configured
            telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
            if telegram_chat_id:
                try:
                    from telegram_sender import send_ranking_to_telegram
                    print(f"\n📱 Sending ranking to Telegram (chat_id: {telegram_chat_id})...")
                    send_ranking_to_telegram(telegram_chat_id, resposta_final.content, TEMA)
                except Exception as e:
                    print(f"⚠️  ERROR: Error sending Telegram: {e}")
                    print("💡 Check if TELEGRAM_BOT_TOKEN is configured in .env")

if __name__ == "__main__":
    asyncio.run(run_agent())
