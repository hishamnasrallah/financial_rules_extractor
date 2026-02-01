#!/usr/bin/env python
"""
Simple test script for CLI extraction.
Run this to test the Financial Rules Extraction Agent.
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("Financial Rules Extraction Agent - Test")
print("=" * 60)
print()

# Test URL
test_url = "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/fd30f9c7-8606-4367-bb22-a9a700f2d952/1"
test_name = "Saudi Civil Service Law"

print(f"📄 Document: {test_name}")
print(f"🔗 URL: {test_url}")
print()

# Initialize agent
print("⏳ Initializing agent...")
try:
    from src.agent import FinancialRulesAgent
    from src.config import config
    
    # Validate config
    config.validate()
    
    agent = FinancialRulesAgent()
    print("✅ Agent initialized successfully")
    print()
except Exception as e:
    print(f"❌ Failed to initialize agent: {e}")
    print()
    print("💡 Tips:")
    print("  1. Make sure .env file exists with AIXPLAIN_API_KEY")
    print("  2. Activate your virtual environment")
    print("  3. Install dependencies: pip install -r requirements.txt")
    sys.exit(1)

# Process document
print("⏳ Processing document...")
print("   This may take 10-30 seconds depending on configuration...")
print()

try:
    result = agent.process_document(
        name=test_name,
        url=test_url,
        use_rag=True  # Enable RAG
    )
    
    print("=" * 60)
    print("✅ EXTRACTION COMPLETE")
    print("=" * 60)
    print()
    
    # Display statistics
    stats = result.statistics
    
    print("📊 Statistics:")
    print(f"   Total Rules: {stats.get('total_rules', 0)}")
    print(f"   Processing Time: {result.processing_time_seconds:.2f} seconds")
    print()
    
    print("📋 Rules by Track:")
    for track, count in stats.get('rules_by_track', {}).items():
        if count > 0:
            print(f"   - {track.title()}: {count}")
    print()
    
    print("🔍 Gaps Identified:")
    print(f"   Total Gaps: {stats.get('total_gaps', 0)}")
    if stats.get('total_gaps', 0) > 0:
        gap_types = stats.get('gaps_by_type', {})
        for gap_type, count in gap_types.items():
            if count > 0:
                print(f"   - {gap_type.title()}: {count}")
    print()
    
    print("⚙️  Configuration:")
    print(f"   RAG Enabled: {stats.get('rag_enabled', False)}")
    print(f"   Chunks Indexed: {stats.get('num_chunks_indexed', 0)}")
    print(f"   Storage Type: {stats.get('storage_type', 'unknown')}")
    print()
    
    # Show sample rules
    if result.extracted_rules:
        print("📝 Sample Extracted Rules:")
        for i, rule in enumerate(result.extracted_rules[:3], 1):
            print(f"\n   Rule {i}:")
            print(f"   Text: {rule.text_ar[:100]}...")
            print(f"   Track: {rule.track_id or 'unmapped'}")
            print(f"   Confidence: {rule.mapping_confidence:.2f}")
    
    print()
    print("=" * 60)
    
    # Export results
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    import json
    from datetime import datetime
    
    output_file = output_dir / f"extraction_{int(datetime.now().timestamp())}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result.dict(), f, ensure_ascii=False, indent=2, default=str)
    
    print(f"💾 Results saved to: {output_file}")
    print()
    
    # Success summary
    if stats.get('total_rules', 0) > 0:
        print("✅ SUCCESS! Rules extracted successfully.")
    else:
        print("⚠️  WARNING: No rules extracted. This might indicate:")
        print("   - Document format issues")
        print("   - Need to adjust extraction patterns")
        print("   - LLM configuration needed")
    
    print()
    print("🎉 Test complete!")
    
except KeyboardInterrupt:
    print("\n\n⏸️  Test interrupted by user")
    sys.exit(130)
except Exception as e:
    print(f"\n❌ ERROR during extraction: {e}")
    print()
    import traceback
    traceback.print_exc()
    print()
    print("💡 Check logs above for details")
    sys.exit(1)
