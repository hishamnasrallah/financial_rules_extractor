"""
Example script demonstrating the Financial Rules Extraction Agent.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.agent import FinancialRulesAgent
from src.models import DocumentType
from src.tracks import TracksRepository

def main():
    """Run example extraction."""
    
    print("=" * 80)
    print("Financial Rules Extraction Agent - Example")
    print("=" * 80)
    print()
    
    # Get API key
    api_key = os.getenv("AIXPLAIN_API_KEY")
    
    if not api_key:
        print("❌ Error: AIXPLAIN_API_KEY not found in environment.")
        print("Please set it in your .env file.")
        return
    
    print("✓ API key found")
    print()
    
    # Initialize agent
    print("Initializing agent...")
    agent = FinancialRulesAgent(api_key=api_key)
    print("✓ Agent initialized")
    print()
    
    # Display available tracks
    print("Available Financial Tracks:")
    print("-" * 80)
    tracks = TracksRepository.get_all_tracks()
    for track_id, track in tracks.items():
        print(f"\n{track.name_ar} ({track.name_en})")
        print(f"  Track ID: {track_id}")
        print(f"  Current Rules: {len(track.current_rules)}")
    print()
    print("=" * 80)
    print()
    
    # Example 1: Process a web page
    print("Example 1: Processing a web page document")
    print("-" * 80)
    
    try:
        result = agent.process_document(
            name="نظام الخدمة المدنية",
            url="https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/5fb85c90-8962-402d-b2e7-a9a700f2ad95/1",
            document_type=DocumentType.WEB_PAGE
        )
        
        print(f"\n✓ Processing completed in {result.processing_time_seconds:.2f} seconds")
        print(f"\nResults:")
        print(f"  - Total Rules Extracted: {result.statistics['total_rules']}")
        print(f"  - Gaps Identified: {result.statistics['total_gaps']}")
        print(f"  - Average Confidence: {result.statistics['average_mapping_confidence']:.2f}")
        
        print(f"\nRules by Track:")
        for track, count in result.statistics['rules_by_track'].items():
            print(f"  - {track}: {count}")
        
        if result.extracted_rules:
            print(f"\nFirst 3 Extracted Rules:")
            for i, rule in enumerate(result.extracted_rules[:3], 1):
                print(f"\n  {i}. {rule.text_ar[:100]}...")
                print(f"     Track: {rule.track_id or 'Unmapped'}")
                print(f"     Confidence: {rule.mapping_confidence:.2f}")
        
        if result.gaps:
            print(f"\nFirst 3 Identified Gaps:")
            for i, gap in enumerate(result.gaps[:3], 1):
                print(f"\n  {i}. Type: {gap.gap_type}, Severity: {gap.severity}")
                print(f"     Track: {gap.track_id}")
                print(f"     Rule: {gap.extracted_rule.text_ar[:80]}...")
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nNote: This example requires a valid aiXplain API key and internet connection.")
    
    print()
    print("=" * 80)
    print()
    
    # Example 2: Batch processing
    print("Example 2: Batch processing multiple documents")
    print("-" * 80)
    print()
    print("To process multiple documents, create a JSON config file:")
    print("""
[
  {
    "name": "نظام الخدمة المدنية",
    "url": "https://...",
    "type": "web_page"
  },
  {
    "name": "تعليمات الميزانية",
    "url": "https://...",
    "type": "pdf"
  }
]
    """)
    print("\nThen run:")
    print("  python cli.py batch --config-file documents.json --output report.json")
    print()
    
    print("=" * 80)
    print("\n✓ Example completed!")
    print("\nNext steps:")
    print("  1. Try the CLI: python cli.py extract --name 'Document' --url 'https://...'")
    print("  2. Try the web UI: streamlit run app.py")
    print("  3. Read the documentation: docs/USER_GUIDE.md")
    print()


if __name__ == "__main__":
    main()
