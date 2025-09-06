#!/bin/bash

# WebWatcher Deep Research Demo Launcher
# Starts vLLM server and research UI

set -e

cd "$(dirname "$0")/.." || exit 1

echo "🔬 WebWatcher Deep Research Demo"
echo "================================="

# Check if model is available
MODEL_PATH="$HOME/.cache/huggingface/WebWatcher-7B"
if [ ! -d "$MODEL_PATH" ]; then
    echo "❌ WebWatcher-7B model not found at: $MODEL_PATH"
    echo "Please download the model first"
    exit 1
fi

# Default environment variables
export OPENAI_API_BASE="${OPENAI_API_BASE:-http://127.0.0.1:8004/v1}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-not-needed-for-local}"

# Optional API keys (will fallback to free services if not set)
export GOOGLE_SEARCH_KEY="${GOOGLE_SEARCH_KEY:-}"
export SERPAPI_API_KEY="${SERPAPI_API_KEY:-}"
export SCRAPERAPI_KEY="${SCRAPERAPI_KEY:-}"
export JINA_API_KEY="${JINA_API_KEY:-}"

# Create runs directory
mkdir -p runs/artifacts

echo "📍 Model path: $MODEL_PATH"
echo "🔗 API endpoint: $OPENAI_API_BASE"
echo "🛠️  Search API: $([ -n "$GOOGLE_SEARCH_KEY" ] && echo "Serper (paid)" || echo "DuckDuckGo (free)")"
echo "🌐 Scraper API: $([ -n "$SCRAPERAPI_KEY" ] && echo "ScraperAPI (paid)" || echo "Direct requests")"
echo ""

# Check if vLLM server is running
echo "🔍 Checking if model server is running..."
if curl -s "$OPENAI_API_BASE/models" >/dev/null 2>&1; then
    echo "✅ Model server is running"
else
    echo "❌ Model server not responding at $OPENAI_API_BASE"
    echo ""
    echo "🚀 To start the model server, run in another terminal:"
    echo ""
    echo "pip install vllm"
    echo "python -m vllm.entrypoints.openai.api_server \\"
    echo "  --host 127.0.0.1 --port 8004 \\"
    echo "  --model $MODEL_PATH \\"
    echo "  --dtype auto --max-model-len 32768 \\"
    echo "  --gpu-memory-utilization 0.90 \\"
    echo "  --trust-remote-code \\"
    echo "  --served-model-name webwatcher"
    echo ""
    read -p "Press Enter once the server is running..."
fi

# Install required packages
echo "📦 Installing required packages..."
pip install -q duckduckgo-search trafilatura beautifulsoup4 gradio qwen-agent || {
    echo "❌ Failed to install packages"
    exit 1
}

echo "🌐 Starting research UI at:"
echo "   Local:  http://localhost:7860" 
echo "   LAN:    http://192.168.68.145:7860"
echo "🔬 You can now ask research questions and see full logs!"
echo ""
echo "Example queries:"
echo "- 'WebWatcher deep research agent capabilities and benchmarks'"
echo "- 'Latest developments in large language models'"  
echo "- 'Climate change impact on coral reefs: recent studies'"
echo ""

# Start the UI
python demos/web_ui_research.py