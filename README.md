## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Ollama (required for local models)

The system uses **local models by default** (no external APIs required):

```bash
# Install Ollama: https://ollama.ai
# macOS:
brew install ollama

# Linux:
curl -fsSL https://ollama.ai/install.sh | sh

# Download required models:
ollama pull deepseek-r1:7b
ollama pull nomic-embed-text
```

### 3. Configure environment variables (optional)

The system works **without a `.env` file** using local models by default. If you want to customize, create a `.env` file:

#### Local models (default - recommended)
```env
# These are the defaults, no need to set if you keep them
LLM_PROVIDER=deepseek-local
DEEPSEEK_MODEL=deepseek-r1:7b
OLLAMA_BASE_URL=http://localhost:11434

EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL=nomic-embed-text

# Paper sources (comma-separated)
# Options: arxiv, semantic_scholar
PAPER_SOURCES=arxiv,semantic_scholar
MAX_PAPERS=15

# Tech news topic (default: "artificial intelligence machine learning")
TECH_NEWS_TOPIC=artificial intelligence machine learning
```

#### Use OpenAI (optional)
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

EMBEDDING_PROVIDER=openai
```

#### Use Gemini (optional)
```env
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your-google-api-key-here
GEMINI_MODEL=gemini-pro

EMBEDDING_PROVIDER=gemini
```

**Note**: You must configure BOTH `LLM_PROVIDER` and `EMBEDDING_PROVIDER` when using external APIs.

## 📋 Supported Providers

### LLM (chat models)

1. **DeepSeek Local** (`LLM_PROVIDER=deepseek-local`) - **DEFAULT**
   - Requires: Ollama installed (`https://ollama.ai`)
   - Default model: `deepseek-r1:7b`
   - Other models: `deepseek-chat`, `deepseek-coder`, `llama3.2`, `mistral`, etc.
   - **Advantages**: No cost, no rate limits, full privacy, works offline

2. **OpenAI** (`LLM_PROVIDER=openai`) - optional
   - Requires: `OPENAI_API_KEY`
   - Models: `gpt-4o-mini`, `gpt-4o`, `gpt-3.5-turbo`, etc.

3. **Google Gemini** (`LLM_PROVIDER=gemini`) - optional
   - Requires: `GOOGLE_API_KEY` (get it at https://makersuite.google.com/app/apikey)
   - Valid models: `gemini-pro`, `gemini-1.5-flash`, `gemini-1.5-pro`
   - **Important**: Also set `EMBEDDING_PROVIDER=gemini` to use Gemini embeddings

### Embeddings

1. **Local** (`EMBEDDING_PROVIDER=local`) - **DEFAULT**
   - Requires: Ollama installed
   - Default model: `nomic-embed-text`
   - Other options: `all-minilm`, `mxbai-embed-large`, `bge-large`, etc.
   - **Advantages**: No cost, no rate limits, full privacy

2. **OpenAI** (`EMBEDDING_PROVIDER=openai`) - optional
   - Model: `text-embedding-3-small`

3. **Google Gemini** (`EMBEDDING_PROVIDER=gemini`) - optional
   - Model: `models/embedding-001`

## 🎯 How to Use

### Run the agent

```bash
python main.py
```

The agent will:
1. Connect to the MCP server
2. Fetch recent technology papers from the configured sources
3. Create embeddings and index them into the RAG store
4. Query the vector database to find innovations
5. Generate a Top 5 ranking of the most relevant tech research
6. **Send the result via Telegram** (if configured – see below)

### 📱 Send results via Telegram

The system can automatically send the rankings via Telegram.

**Quick setup:**
1. Create a bot with [@BotFather](https://t.me/BotFather) on Telegram
2. Get your `chat_id` (see detailed instructions below)
3. Configure your `.env` file:
   ```env
   TELEGRAM_BOT_TOKEN=your_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```
4. Run the agent – it will send the ranking automatically

**📖 See `TELEGRAM_SETUP.md` for detailed instructions**

**Advantages:**
- ✅ Much simpler and more reliable than WhatsApp
- ✅ Official Telegram API
- ✅ Supports Markdown formatting
- ✅ Works on servers/background processes
- ✅ Free and no rate limits for normal use

### Customize the tech news topic

Configure in `.env`:

```env
# Tech news topic to search for
TECH_NEWS_TOPIC=large language models transformers
# or
TECH_NEWS_TOPIC=quantum computing
# or
TECH_NEWS_TOPIC=computer vision deep learning
```

## 🔧 Advanced Configuration

### Use different models

You can specify different models in `.env`:

```env
# OpenAI
OPENAI_MODEL=gpt-4o

# Gemini
GEMINI_MODEL=gemini-1.5-pro

# DeepSeek Local
DEEPSEEK_MODEL=deepseek-chat:7b
```

### Check Ollama

Make sure Ollama is running (required for local models):

```bash
# Check if it's running
curl http://localhost:11434/api/tags

# If not running, start it:
ollama serve

# Download required models (if not already installed)
ollama pull deepseek-r1:7b
ollama pull nomic-embed-text

# List available models
ollama list
```

## 🐛 Troubleshooting

### Error: "Quota exceeded"
- **OpenAI**: Check your account at https://platform.openai.com/account/billing
- **Quick fix**: Use `LLM_PROVIDER=gemini` or `LLM_PROVIDER=deepseek-local`

### Error: "Ollama is not running"
- Make sure Ollama is installed and running
- Check: `ollama serve` or start the Ollama service

### Error: "GOOGLE_API_KEY not found"
- Get a key at: https://makersuite.google.com/app/apikey
- Add to `.env`: `GOOGLE_API_KEY=your-key-here`

### Error: "Gemini model not found (404)"
- The model `gemini-1.5-flash` may not be available in your region/account
- **Solution**: Use `GEMINI_MODEL=gemini-pro` in `.env` (most compatible)
- Or try: `gemini-1.0-pro`, `gemini-1.5-pro`

### Error: "Gemini quota exceeded"
- Check your usage: https://ai.dev/usage?tab=rate-limit
- **Quick solution**: Use local models with Ollama:
  ```env
  LLM_PROVIDER=deepseek-local
  EMBEDDING_PROVIDER=local
  ```

## 📦 Project Structure

```text
papersthisweek/
├── main.py              # MCP client that orchestrates the flow
├── mcp_server.py        # MCP server exposing RAG tools
├── paper_sources.py     # Academic/tech sources integration
├── telegram_sender.py   # Telegram integration
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (not committed)
└── README.md            # This file
```

## 🔄 System Flow

1. **Client** (`main.py`) connects to the MCP server
2. **Server** (`mcp_server.py`) exposes tools:
   - `update_knowledge_base`: downloads papers and creates embeddings
   - `query_rag`: performs similarity search in the vector database
3. **Client** uses the configured LLM to generate the final ranking

## 📝 Notes

- The vector database is kept in memory while the server is running
- Embeddings are created on-demand when you call `update_knowledge_base`
- Focused on tech news: it searches only in academic tech sources
- You can mix providers (e.g., OpenAI for embeddings, Gemini for LLM)
