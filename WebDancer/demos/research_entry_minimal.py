"""
WebWatcher Deep Research - Minimal Agent-Free Implementation
Direct orchestration without qwen-agent framework
"""

import os
import json
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Import our real tools
from tools_ext.free_search import search_web, search_images
from tools_ext.extractors import visit_and_extract

class MinimalResearchOrchestrator:
    """
    Minimal research orchestrator using OpenAI-compatible API
    No agent framework - direct tool orchestration
    """
    
    def __init__(self, 
                 api_base: str = "http://192.168.68.145:8004/v1",
                 api_key: str = "local-any",
                 model: str = "webwatcher"):
        
        self.api_base = api_base
        self.api_key = api_key
        self.model = model
        
        # Create runs directory
        self.runs_dir = Path("./runs")
        self.runs_dir.mkdir(exist_ok=True)
        
        # Test connection
        try:
            response = requests.get(f"{api_base}/models", timeout=5)
            if response.status_code == 200:
                print(f"✅ Connected to model server at {api_base}")
            else:
                print(f"⚠️ Model server responded with status {response.status_code}")
        except Exception as e:
            print(f"❌ Cannot connect to model server: {e}")
    
    def call_model(self, prompt: str, max_tokens: int = 300) -> str:
        """Call the model via OpenAI-compatible API"""
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.3
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
            else:
                return f"Error: API returned {response.status_code}"
                
        except Exception as e:
            return f"Error calling model: {str(e)}"
    
    def search_and_gather(self, query: str, max_sources: int = 5) -> List[Dict[str, Any]]:
        """Search web and gather content from top sources"""
        
        print(f"🔍 Searching for: {query}")
        search_results = search_web(query, num_results=8)
        
        if not search_results:
            return []
        
        gathered_sources = []
        
        for i, result in enumerate(search_results[:max_sources], 1):
            print(f"🌐 Visiting source {i}/{max_sources}: {result['title']}")
            
            try:
                content = visit_and_extract(result['link'])
                
                if content['success']:
                    source = {
                        'title': result['title'],
                        'url': result['link'],
                        'snippet': result['snippet'],
                        'content': content['content'][:3000],  # Limit content length
                        'extraction_method': content['method'],
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    if 'html_artifact' in content:
                        source['artifact'] = content['html_artifact']['filename']
                    
                    gathered_sources.append(source)
                    print(f"✅ Extracted {len(content['content'])} chars from {result['title']}")
                else:
                    print(f"❌ Failed to extract content from {result['link']}: {content['error']}")
                    
            except Exception as e:
                print(f"❌ Error visiting {result['link']}: {str(e)}")
        
        print(f"📊 Successfully gathered content from {len(gathered_sources)} sources")
        return gathered_sources
    
    def synthesize_research(self, query: str, sources: List[Dict[str, Any]]) -> str:
        """Use model to synthesize research from gathered sources"""
        
        print("🧠 Synthesizing research with WebWatcher...")
        
        # Build context from sources
        source_context = ""
        for i, source in enumerate(sources, 1):
            source_context += f"\n\nSource {i}: {source['title']}\nURL: {source['url']}\nContent: {source['content']}\n"
        
        # Create research prompt
        research_prompt = f"""You are a deep research agent. Based on the following sources, provide a comprehensive research report on: {query}

Please structure your response as:

## Summary
Brief overview of findings

## Key Findings
- Main points with citations [Source X]
- Use direct quotes where relevant

## Contradictions/Uncertainties  
Note any conflicting information between sources

## Sources
Full citations with URLs

Sources gathered:
{source_context}

Research Question: {query}"""

        # Get model response
        synthesis = self.call_model(research_prompt, max_tokens=1000)
        
        print("✅ Research synthesis completed")
        return synthesis
    
    def conduct_research(self, query: str) -> Dict[str, Any]:
        """Conduct full research cycle: search → gather → synthesize"""
        
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = self.runs_dir / session_id
        session_dir.mkdir(exist_ok=True)
        
        start_time = time.time()
        
        print(f"🔬 Starting research session: {session_id}")
        print(f"📝 Query: {query}")
        print("=" * 60)
        
        try:
            # Step 1: Search and gather sources
            sources = self.search_and_gather(query, max_sources=5)
            
            if not sources:
                return {
                    'session_id': session_id,
                    'query': query,
                    'error': 'No sources found',
                    'duration': time.time() - start_time
                }
            
            # Step 2: Synthesize research  
            research_report = self.synthesize_research(query, sources)
            
            # Step 3: Save artifacts
            self._save_artifacts(session_dir, query, research_report, sources)
            
            duration = time.time() - start_time
            
            print(f"🎉 Research completed in {duration:.1f}s")
            print(f"📁 Results saved to: {session_dir}")
            
            return {
                'session_id': session_id,
                'query': query,
                'report': research_report,
                'sources': sources,
                'duration': duration,
                'artifacts_dir': str(session_dir)
            }
            
        except Exception as e:
            print(f"❌ Research failed: {str(e)}")
            return {
                'session_id': session_id,
                'query': query,
                'error': str(e),
                'duration': time.time() - start_time
            }
    
    def _save_artifacts(self, session_dir: Path, query: str, report: str, sources: List[Dict[str, Any]]):
        """Save research artifacts"""
        
        # Save final report
        report_file = session_dir / "research_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# Research Report: {query}\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(report)
        
        # Save sources
        sources_file = session_dir / "sources.json" 
        with open(sources_file, 'w', encoding='utf-8') as f:
            json.dump(sources, f, indent=2, ensure_ascii=False)
        
        # Save metadata
        metadata = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'num_sources': len(sources),
            'report_length': len(report)
        }
        
        metadata_file = session_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"💾 Artifacts saved:")
        print(f"   📄 {report_file}")
        print(f"   📚 {sources_file}")
        print(f"   📋 {metadata_file}")

# Simple function interface for the UI
def deep_research(query: str) -> Dict[str, Any]:
    """Simple function interface for research"""
    
    orchestrator = MinimalResearchOrchestrator()
    return orchestrator.conduct_research(query)

# Test function
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        query = "WebWatcher deep research agent capabilities and benchmarks"
        print(f"Using default query: {query}")
    else:
        query = " ".join(sys.argv[1:])
    
    result = deep_research(query)
    
    if 'error' in result:
        print(f"Research failed: {result['error']}")
    else:
        print(f"Research completed successfully!")
        print(f"Session: {result['session_id']}")
        print(f"Duration: {result['duration']:.1f}s")
        print(f"Sources: {len(result['sources'])}")
        if result.get('artifacts_dir'):
            print(f"Saved to: {result['artifacts_dir']}")