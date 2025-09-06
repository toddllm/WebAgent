# WebWatcher Deep Research Demo

Complete setup for running WebWatcher-7B as a deep research agent with real tool integration.

## Quick Start

### 1. Serve WebWatcher-7B Model

Start vLLM server in one terminal:

```bash
pip install vllm
python -m vllm.entrypoints.openai.api_server \
  --host 127.0.0.1 --port 8004 \
  --model ~/.cache/huggingface/WebWatcher-7B \
  --dtype auto --max-model-len 32768 \
  --gpu-memory-utilization 0.90 \
  --trust-remote-code \
  --served-model-name webwatcher
```

### 2. Start Research Demo

In another terminal:

```bash
cd WebAgent
bash WebDancer/scripts/run_deep_research.sh
```

This will:
- Install required dependencies
- Check model server connection
- Launch Gradio UI at http://localhost:7860

### 3. Use the Research Agent

1. Open http://localhost:7860 in your browser
2. Enter a research query (examples provided in UI)
3. Watch the agent search, visit pages, and compile a research report
4. Check `./runs/YYYYMMDD_HHMMSS/` for saved artifacts

## Architecture

### Real Tools (No Mocks)

**Search**: 
- Primary: Serper API (if `GOOGLE_SEARCH_KEY` set)
- Fallback: DuckDuckGo (free)

**Web Extraction**:
- Primary: ScraperAPI (if `SCRAPERAPI_KEY` set) 
- Fallback: Direct requests with headers
- Content parsing: trafilatura + BeautifulSoup

**Image Search**:
- Primary: SerpAPI (if `SERPAPI_API_KEY` set)
- Fallback: DuckDuckGo Images (free)

### File Structure

```
WebAgent/
├── .env.example                           # Environment variables template
├── WebDancer/
│   ├── demos/
│   │   ├── presets/deep_research.yaml     # Research agent configuration  
│   │   ├── tools_ext/                     # Extended tool implementations
│   │   │   ├── free_search.py            # Search with API fallbacks
│   │   │   └── extractors.py             # Content extraction tools
│   │   ├── research_entry.py             # Headless research runner
│   │   └── web_ui_research.py            # Gradio web interface
│   └── scripts/
│       └── run_deep_research.sh          # Launch script
├── extras/research/requirements.txt       # Additional dependencies
└── runs/                                 # Research artifacts (auto-created)
    ├── artifacts/                        # Saved HTML pages
    └── YYYYMMDD_HHMMSS/                  # Research session results
        ├── research_report.md
        ├── metadata.json
        └── raw_responses.json
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your API keys (optional - free fallbacks work)
```

**Required**: Model server endpoint
**Optional**: Search/scraping API keys (will use free services as fallback)

## API Keys (All Optional)

- **Serper**: Google search results ($5/1000 queries)
- **SerpAPI**: Google search + images ($75/5000 queries)  
- **ScraperAPI**: JS-heavy sites ($29/250k requests)
- **Jina Reader**: Clean article extraction ($20/1M requests)

Without keys: Uses DuckDuckGo search + direct HTTP requests.

## Examples

### CLI Research
```bash
cd WebAgent/WebDancer/demos
python research_entry.py "Climate change impact on coral reefs"
```

### Web UI Research  
1. Start server: `bash WebDancer/scripts/run_deep_research.sh`
2. Open: http://localhost:7860
3. Ask: "Latest developments in large language models"
4. Watch: Agent searches → visits pages → extracts content → cites sources

## Model Compatibility

- **Tested**: WebWatcher-7B (downloaded)
- **Compatible**: Any Qwen-based instruct model served via vLLM
- **Alternative**: Use DashScope cloud API by setting `DASHSCOPE_API_KEY`

## What You'll See

1. **Real web searches** (DuckDuckGo or Google via API)
2. **Actual webpage visits** with content extraction
3. **Source attribution** with URLs and quotes
4. **Artifact saving** (HTML pages, final reports)
5. **Research methodology** visible in agent responses
6. **Multi-step reasoning** as agent plans and executes research

No mocked tools or fake responses - everything uses real APIs and actual web content.