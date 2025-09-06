"""
WebWatcher Deep Research Agent - Web UI
Simple Gradio interface for research agent
"""

import os
import sys
import gradio as gr
from typing import Tuple
import traceback

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from research_entry_minimal import deep_research

class ResearchUI:
    def __init__(self):
        pass
    
    def initialize_agent(self) -> Tuple[str, str]:
        """Initialize the research system"""
        try:
            # Test connection to model server
            import requests
            response = requests.get("http://127.0.0.1:8004/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('model_loaded'):
                    status = "✅ Research system ready"
                    model_info = "WebWatcher-7B loaded at http://127.0.0.1:8004"
                else:
                    status = "⏳ Model loading..."
                    model_info = "Please wait for model to load"
            else:
                status = "❌ Model server not responding"
                model_info = "Check if server is running"
        except Exception as e:
            status = f"❌ Connection failed: {str(e)}"
            model_info = "Model server unavailable"
        
        return status, model_info
    
    def conduct_research(self, query: str, progress=gr.Progress()) -> Tuple[str, str, str]:
        """Conduct research and return results"""
        
        if not query.strip():
            return "Please enter a research query.", "", ""
        
        try:
            progress(0.1, desc="Starting research...")
            
            # Use minimal research orchestrator
            result = deep_research(query)
            
            if 'error' in result:
                return f"❌ Research failed: {result['error']}", "", ""
            
            progress(0.9, desc="Finalizing results...")
            
            # Format results
            summary = f"""## Research Summary
**Query:** {result['query']}
**Session ID:** {result['session_id']}
**Duration:** {result['duration']:.1f} seconds
**Sources:** {len(result.get('sources', []))} websites visited
**Artifacts saved to:** {result.get('artifacts_dir', 'N/A')}
"""
            
            report = result['report']
            
            # Create download info
            artifacts_info = ""
            if result.get('artifacts_dir'):
                artifacts_info = f"""### 📁 Saved Artifacts
- Research Report: `{result['artifacts_dir']}/research_report.md`
- Sources Data: `{result['artifacts_dir']}/sources.json`  
- Metadata: `{result['artifacts_dir']}/metadata.json`
- HTML Pages: `./runs/artifacts/` (if pages were visited)

You can find all files in the `{result['artifacts_dir']}` directory."""
            
            progress(1.0, desc="Research complete!")
            
            return summary, report, artifacts_info
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            return f"❌ Research failed: {str(e)}\n\nDebug info:\n{error_trace}", "", ""
    
    def create_interface(self):
        """Create the Gradio interface"""
        
        with gr.Blocks(title="WebWatcher Deep Research Agent", theme=gr.themes.Soft()) as interface:
            
            gr.HTML("""
            <div style="text-align: center; padding: 20px;">
                <h1>🔬 WebWatcher Deep Research Agent</h1>
                <p>Multi-modal research with web search, content extraction, and source verification</p>
            </div>
            """)
            
            # Status section
            with gr.Row():
                with gr.Column(scale=1):
                    agent_status = gr.Textbox(
                        label="🤖 Agent Status", 
                        value="Initializing...",
                        interactive=False
                    )
                with gr.Column(scale=1):
                    model_info = gr.Textbox(
                        label="🔧 Model Info",
                        value="Loading...",
                        interactive=False
                    )
            
            # Initialize status
            interface.load(
                fn=self.initialize_agent,
                outputs=[agent_status, model_info]
            )
            
            gr.Markdown("## 📝 Research Query")
            
            # Research input
            with gr.Row():
                with gr.Column(scale=4):
                    query_input = gr.Textbox(
                        label="Enter your research question",
                        placeholder="Example: Latest developments in large language models and their applications",
                        lines=2,
                        value="WebWatcher deep research agent capabilities and benchmarks"
                    )
                with gr.Column(scale=1):
                    research_btn = gr.Button(
                        "🔍 Start Research", 
                        variant="primary",
                        size="lg"
                    )
            
            # Example queries
            with gr.Row():
                gr.Examples(
                    examples=[
                        ["Latest breakthroughs in quantum computing applications"],
                        ["Climate change impact on coral reefs: recent studies and findings"], 
                        ["Ethical implications of AI in healthcare decision-making"],
                        ["Economic effects of remote work on urban development"],
                        ["Recent advances in gene therapy for rare diseases"]
                    ],
                    inputs=query_input,
                    label="Example Research Topics"
                )
            
            gr.Markdown("## 📊 Research Results")
            
            # Results section
            with gr.Row():
                with gr.Column(scale=1):
                    summary_output = gr.Markdown(
                        label="Research Summary",
                        value="Research results will appear here..."
                    )
                with gr.Column(scale=2):
                    report_output = gr.Markdown(
                        label="Full Report", 
                        value="Full research report will appear here..."
                    )
            
            # Artifacts info
            artifacts_output = gr.Markdown(
                label="📁 Saved Files",
                value="Information about saved files will appear here..."
            )
            
            # Wire up the interface
            research_btn.click(
                fn=self.conduct_research,
                inputs=[query_input],
                outputs=[summary_output, report_output, artifacts_output],
                show_progress=True
            )
            
            # Allow Enter key to trigger research
            query_input.submit(
                fn=self.conduct_research,
                inputs=[query_input],
                outputs=[summary_output, report_output, artifacts_output],
                show_progress=True
            )
            
            # Footer
            gr.HTML("""
            <div style="text-align: center; padding: 20px; color: #666;">
                <p>Powered by WebWatcher-7B • Built on WebDancer Framework</p>
                <p>Research artifacts are automatically saved to <code>./runs/</code> directory</p>
            </div>
            """)
        
        return interface

def main():
    """Launch the research UI"""
    
    # Check environment
    print("🔬 Starting WebWatcher Deep Research Agent UI")
    print(f"📍 Working directory: {os.getcwd()}")
    
    # Create UI
    ui = ResearchUI()
    interface = ui.create_interface()
    
    # Launch on LAN
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        inbrowser=False
    )

if __name__ == "__main__":
    main()