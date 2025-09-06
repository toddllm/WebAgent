"""
WebWatcher Deep Research Agent - Entry Point
Uses WebDancer's agent framework with research-specific tools
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add current directory to path to import tools_ext
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools_ext.free_search import search_web, search_images
from tools_ext.extractors import visit_and_extract, extract_with_jina

# Import WebDancer components
from qwen_agent.agents import Assistant
from llm.oai import TextChatAtOAI

class DeepResearchAgent:
    """
    Deep Research Agent using WebDancer's framework
    """
    
    def __init__(self, 
                 model_endpoint: str = "http://127.0.0.1:8004/v1",
                 model_key: str = "not-needed-for-local",
                 max_iterations: int = 12):
        
        self.runs_dir = Path("./runs")
        self.runs_dir.mkdir(exist_ok=True)
        
        # Initialize LLM
        self.llm_cfg = TextChatAtOAI({
            'model': 'local',
            'model_type': 'oai',
            'model_server': model_endpoint,
            'api_key': model_key,
            'generate_cfg': {
                'temperature': 0.3,
                'top_p': 0.9,
                'max_tokens': 4096,
                'stream': False
            }
        })
        
        # Initialize agent with research tools
        self.agent = Assistant(
            llm=self.llm_cfg,
            name="Deep Research Agent",
            description="Multi-modal research agent with web search and content extraction",
            function_list=['search', 'visit', 'image_search'],
            system_message=self._get_system_message()
        )
        
        self.max_iterations = max_iterations
        
        # Register custom tools
        self._register_tools()
    
    def _get_system_message(self) -> str:
        return """You are a deep research agent with access to web search, webpage content extraction, and image search tools.

Your research methodology:
1. Plan multi-hop queries to gather comprehensive information
2. Search for relevant sources and visit key pages to extract content
3. Collect quotes, facts, and data with proper URL attribution
4. Cross-reference sources to identify contradictions or confirmations
5. Synthesize findings into a structured report with citations

Research quality standards:
- Always include direct quotes with URLs when making claims
- Flag contradictory information between sources
- Prefer primary sources and recent information when available
- Note when sources are unavailable or blocked
- Track publication dates and author credentials when available

Tools available:
- search(query): Search the web for relevant information
- visit(url): Visit a webpage and extract its content
- image_search(query): Search for relevant images

Output format:
- Start with a TL;DR summary
- Organize findings by topic/theme  
- Include a "Contradictions/Uncertainties" section if relevant
- End with full citations and methodology notes

Never hallucinate URLs or make unsupported claims. Always cite your sources."""

    def _register_tools(self):
        """Register custom research tools"""
        
        def search_tool(query: str) -> str:
            """Search the web for information"""
            try:
                results = search_web(query, num_results=8)
                if not results:
                    return "No search results found."
                
                formatted_results = []
                for i, result in enumerate(results, 1):
                    formatted_results.append(
                        f"{i}. {result['title']}\n"
                        f"   URL: {result['link']}\n"
                        f"   Snippet: {result['snippet'][:200]}...\n"
                        f"   Source: {result['source']}\n"
                    )
                
                return "\n".join(formatted_results)
            except Exception as e:
                return f"Search failed: {str(e)}"
        
        def visit_tool(url: str) -> str:
            """Visit a webpage and extract its content"""
            try:
                result = visit_and_extract(url)
                
                if not result['success']:
                    return f"Failed to visit {url}: {result['error']}"
                
                content = result['content']
                title = result['title']
                
                # Truncate content if too long
                if len(content) > 4000:
                    content = content[:4000] + "...\n[Content truncated]"
                
                response = f"Page: {title}\nURL: {url}\n\nContent:\n{content}"
                
                # Note artifact saved
                if 'html_artifact' in result:
                    response += f"\n\n[HTML saved to: {result['html_artifact']['filename']}]"
                
                return response
            except Exception as e:
                return f"Failed to visit {url}: {str(e)}"
        
        def image_search_tool(query: str) -> str:
            """Search for relevant images"""
            try:
                results = search_images(query, num_results=6)
                if not results:
                    return "No image search results found."
                
                formatted_results = []
                for i, result in enumerate(results, 1):
                    formatted_results.append(
                        f"{i}. {result['title']}\n"
                        f"   Image URL: {result['image_url']}\n"
                        f"   Source: {result.get('source_url', 'N/A')}\n"
                    )
                
                return "\n".join(formatted_results)
            except Exception as e:
                return f"Image search failed: {str(e)}"
        
        # Register tools with agent - add to function_list first
        from qwen_agent.tools import BaseTool
        
        class SearchTool(BaseTool):
            name = "search"
            description = "Search the web for information"
            parameters = [{"name": "query", "type": "string", "description": "Search query"}]
            
            def call(self, params):
                return search_tool(params.get("query", ""))
        
        class VisitTool(BaseTool):
            name = "visit" 
            description = "Visit a webpage and extract content"
            parameters = [{"name": "url", "type": "string", "description": "URL to visit"}]
            
            def call(self, params):
                return visit_tool(params.get("url", ""))
        
        class ImageSearchTool(BaseTool):
            name = "image_search"
            description = "Search for images"
            parameters = [{"name": "query", "type": "string", "description": "Image search query"}]
            
            def call(self, params):
                return image_search_tool(params.get("query", ""))
        
        # Register tools properly
        self.agent.function_map['search'] = SearchTool()
        self.agent.function_map['visit'] = VisitTool()
        self.agent.function_map['image_search'] = ImageSearchTool()

    def research(self, query: str, save_artifacts: bool = True) -> Dict[str, Any]:
        """
        Conduct deep research on a query
        """
        
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = self.runs_dir / session_id
        session_dir.mkdir(exist_ok=True)
        
        print(f"🔬 Starting deep research session: {session_id}")
        print(f"📍 Query: {query}")
        print(f"💾 Artifacts will be saved to: {session_dir}")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # Start research conversation
            messages = [{'role': 'user', 'content': f"Research this topic thoroughly: {query}"}]
            
            response = []
            iteration = 0
            
            while iteration < self.max_iterations:
                iteration += 1
                print(f"\n🔄 Research iteration {iteration}/{self.max_iterations}")
                
                # Get agent response
                agent_response = self.agent.run(messages=messages)
                
                if agent_response:
                    response.append(agent_response)
                    print(f"📝 Agent response length: {len(str(agent_response))} chars")
                    
                    # Check if research seems complete
                    if self._is_research_complete(str(agent_response)):
                        print("✅ Research appears complete")
                        break
                else:
                    print("⚠️ Empty response from agent")
                    break
            
            # Combine all responses
            final_report = self._compile_report(response, query)
            
            # Save artifacts
            if save_artifacts:
                self._save_research_artifacts(session_dir, query, final_report, response)
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"\n✅ Research completed in {duration:.1f} seconds")
            print(f"📊 Final report length: {len(final_report)} characters")
            
            return {
                'session_id': session_id,
                'query': query,
                'report': final_report,
                'duration': duration,
                'iterations': iteration,
                'artifacts_dir': str(session_dir) if save_artifacts else None
            }
            
        except Exception as e:
            print(f"❌ Research failed: {str(e)}")
            return {
                'session_id': session_id,
                'query': query,
                'error': str(e),
                'duration': time.time() - start_time
            }

    def _is_research_complete(self, response: str) -> bool:
        """Check if research appears to be complete"""
        completion_indicators = [
            "## Citations",
            "## References", 
            "## Sources",
            "## Conclusion",
            "In conclusion",
            "To summarize",
            "## Full Citations"
        ]
        
        response_lower = response.lower()
        return any(indicator.lower() in response_lower for indicator in completion_indicators)

    def _compile_report(self, responses: List[Any], query: str) -> str:
        """Compile final research report from agent responses"""
        
        report_parts = [
            f"# Deep Research Report: {query}",
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]
        
        for i, response in enumerate(responses, 1):
            report_parts.append(f"## Research Phase {i}")
            report_parts.append(str(response))
            report_parts.append("")
        
        return "\n".join(report_parts)

    def _save_research_artifacts(self, session_dir: Path, query: str, report: str, raw_responses: List[Any]):
        """Save research artifacts to session directory"""
        
        # Save final report
        report_file = session_dir / "research_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Save metadata
        metadata = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'iterations': len(raw_responses),
            'report_length': len(report)
        }
        
        metadata_file = session_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        # Save raw responses
        raw_file = session_dir / "raw_responses.json"
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump([str(r) for r in raw_responses], f, indent=2)
        
        print(f"💾 Artifacts saved:")
        print(f"   📄 Report: {report_file}")
        print(f"   📋 Metadata: {metadata_file}")
        print(f"   🗂️  Raw data: {raw_file}")

def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python research_entry.py 'Your research query here'")
        print("Example: python research_entry.py 'Latest developments in quantum computing'")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    
    # Initialize agent
    agent = DeepResearchAgent()
    
    # Run research
    result = agent.research(query)
    
    if 'error' in result:
        print(f"Research failed: {result['error']}")
        sys.exit(1)
    else:
        print(f"\n📋 Research completed successfully!")
        print(f"Session ID: {result['session_id']}")
        if result.get('artifacts_dir'):
            print(f"Results saved to: {result['artifacts_dir']}")

if __name__ == "__main__":
    main()