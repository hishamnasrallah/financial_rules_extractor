"""
Simple Q&A Script - Ask the Agent Anything!
Run this to interact with the Financial Rules Extraction Agent.
"""
import os
from dotenv import load_dotenv
load_dotenv()

from src.tracks import TracksRepository

def show_welcome():
    print("\n" + "="*70)
    print("  💬 Financial Rules Extraction Agent - Q&A Mode")
    print("="*70)
    print("\n👋 Hi! I'm your Financial Rules Extraction Agent.")
    print("   Ask me anything about the system!\n")
    print("📚 Available commands:")
    print("   • 'tracks' - Show available financial tracks")
    print("   • 'salaries' - Show rules for salaries track")
    print("   • 'contracts' - Show rules for contracts track")
    print("   • 'invoices' - Show rules for invoices track")
    print("   • 'help' - Show all commands")
    print("   • 'demo' - Run a quick demo")
    print("   • 'status' - Check system status")
    print("   • 'exit' - Quit\n")

def show_tracks():
    """Show all financial tracks"""
    tracks = TracksRepository.get_all_tracks()
    
    print("\n📋 Available Financial Tracks:\n")
    for track_id, track in tracks.items():
        print(f"  🎯 {track.name_ar} ({track.name_en})")
        print(f"     Track ID: {track_id}")
        print(f"     Definition: {track.definition_ar[:100]}...")
        print(f"     Current Rules: {len(track.current_rules)}\n")

def show_track_rules(track_id):
    """Show rules for a specific track"""
    tracks = TracksRepository.get_all_tracks()
    
    if track_id not in tracks:
        print(f"\n❌ Track '{track_id}' not found")
        print(f"   Available tracks: {', '.join(tracks.keys())}\n")
        return
    
    track = tracks[track_id]
    print(f"\n📊 {track.name_ar} ({track.name_en})\n")
    print(f"Definition: {track.definition_ar}\n")
    print(f"Current Rules ({len(track.current_rules)}):\n")
    
    for i, rule in enumerate(track.current_rules, 1):
        print(f"  {i}. {rule.description}")
        print(f"     Rule ID: {rule.rule_id}\n")

def show_status():
    """Show system status"""
    print("\n🔍 System Status:\n")
    
    # Check API key
    api_key = os.getenv("AIXPLAIN_API_KEY")
    if api_key:
        print("  ✅ API Key: Configured")
    else:
        print("  ⚠️  API Key: Not configured (set in .env file)")
    
    # Check tracks
    tracks = TracksRepository.get_all_tracks()
    print(f"  ✅ Financial Tracks: {len(tracks)} loaded")
    
    # Check components
    try:
        from src.agent import FinancialRulesAgent
        print("  ✅ Agent: Ready")
    except:
        print("  ❌ Agent: Import failed")
    
    try:
        from src.parser import DocumentParser
        print("  ✅ Parser: Ready")
    except:
        print("  ❌ Parser: Import failed")
    
    try:
        from src.rule_extractor import RuleExtractor
        print("  ✅ Rule Extractor: Ready")
    except:
        print("  ❌ Rule Extractor: Import failed")
    
    print()

def show_demo():
    """Run a quick demo"""
    print("\n🎬 Quick Demo:\n")
    
    print("1️⃣ Loading tracks...")
    tracks = TracksRepository.get_all_tracks()
    print(f"   ✓ Loaded {len(tracks)} tracks: {', '.join(tracks.keys())}\n")
    
    print("2️⃣ Sample rule from Salaries track:")
    salaries = tracks['salaries']
    print(f"   \"{salaries.current_rules[0].description}\"\n")
    
    print("3️⃣ How extraction works:")
    print("   a) Parse document (PDF/Web) → Extract text")
    print("   b) Index in aiXplain aiR → Vector storage")
    print("   c) LLM extracts rules → AI-powered extraction")
    print("   d) Map to tracks → Automatic classification")
    print("   e) Identify gaps → Compare with existing rules")
    print("   f) HITL review → Human validation\n")
    
    print("4️⃣ To process a real document:")
    print("   • Web: streamlit run app.py")
    print("   • CLI: python cli.py extract --name 'Doc' --url 'https://...'\n")

def show_help():
    """Show all available commands"""
    print("\n📖 Available Commands:\n")
    
    commands = {
        "tracks": "Show all available financial tracks",
        "salaries": "Show all rules for الرواتب (Salaries) track",
        "contracts": "Show all rules for العقود (Contracts) track",
        "invoices": "Show all rules for الفواتير (Invoices) track",
        "status": "Check system status and configuration",
        "demo": "Run a quick demonstration",
        "help": "Show this help message",
        "clear": "Clear the screen",
        "exit / quit": "Exit the Q&A mode"
    }
    
    for cmd, desc in commands.items():
        print(f"  • {cmd:15} - {desc}")
    
    print("\n💡 You can also ask questions like:")
    print("  • What documents can you process?")
    print("  • How does gap analysis work?")
    print("  • What is the confidence score?")
    print("  • How do I export results?\n")

def handle_question(question):
    """Handle natural language questions"""
    q = question.lower()
    
    # Document-related questions
    if 'document' in q or 'pdf' in q or 'file' in q:
        print("\n📄 Document Processing:\n")
        print("  Supported formats:")
        print("    • PDF files (.pdf)")
        print("    • Web pages (HTML)")
        print("    • Plain text (.txt)")
        print("\n  To process:")
        print("    python cli.py extract --name 'Name' --file 'path/to/file.pdf'")
        print("    python cli.py extract --name 'Name' --url 'https://...'")
        print()
    
    # Gap analysis
    elif 'gap' in q:
        print("\n🔍 Gap Analysis:\n")
        print("  Identifies:")
        print("    • Missing rules: Not implemented in system")
        print("    • Partial coverage: Partially implemented")
        print("    • Conflicting rules: Contradictions")
        print("\n  Severity levels: critical, high, medium, low\n")
    
    # Confidence score
    elif 'confidence' in q or 'score' in q:
        print("\n📊 Confidence Scores:\n")
        print("  Range: 0.0 to 1.0")
        print("    • 0.0-0.5: Low (requires human review)")
        print("    • 0.5-0.7: Medium (likely correct)")
        print("    • 0.7-1.0: High (very likely correct)\n")
    
    # Export results
    elif 'export' in q or 'save' in q:
        print("\n💾 Export Results:\n")
        print("  CLI:")
        print("    python cli.py extract --name 'Doc' --url '...' --output results.json")
        print("\n  Web UI:")
        print("    Go to 'Export' tab and click 'Download as JSON'\n")
    
    # How it works
    elif 'how' in q and 'work' in q:
        show_demo()
    
    # aiXplain
    elif 'aixplain' in q:
        print("\n🤖 aiXplain Integration:\n")
        print("  aiR (Index & Retrieval): Vector-based document storage")
        print("  LLM Models: AI-powered rule extraction")
        print("  Embedding Models: Semantic similarity matching")
        print("  Agent Framework: Multi-step reasoning\n")
    
    else:
        print("\n❓ I'm not sure about that. Try:")
        print("   • Type 'help' for available commands")
        print("   • Type 'demo' for a quick demonstration")
        print("   • Be more specific (e.g., 'How do I export results?')\n")

def main():
    """Main Q&A loop"""
    show_welcome()
    
    while True:
        try:
            question = input("💬 You: ").strip()
            
            if not question:
                continue
            
            # Commands
            if question.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye! To start again, run: python qa_agent.py\n")
                break
            
            elif question.lower() == 'tracks':
                show_tracks()
            
            elif question.lower() == 'salaries':
                show_track_rules('salaries')
            
            elif question.lower() == 'contracts':
                show_track_rules('contracts')
            
            elif question.lower() == 'invoices':
                show_track_rules('invoices')
            
            elif question.lower() == 'status':
                show_status()
            
            elif question.lower() == 'demo':
                show_demo()
            
            elif question.lower() == 'help':
                show_help()
            
            elif question.lower() == 'clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                show_welcome()
            
            else:
                # Try to answer as a question
                handle_question(question)
        
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    main()
