"""
Quick verification script to test all imports.
"""
import sys

print("Testing imports...")

try:
    print("1. Testing config...")
    from src.config import config
    print("   ✓ Config loaded")

    print("2. Testing models...")
    from src.models import Document, ExtractedRule, DocumentType
    print("   ✓ Models loaded")

    print("3. Testing tracks...")
    from src.tracks import TracksRepository
    tracks = TracksRepository.get_all_tracks()
    print(f"   ✓ Tracks loaded ({len(tracks)} tracks)")

    print("4. Testing parser...")
    from src.parser import DocumentParser
    print("   ✓ Parser loaded")

    print("5. Testing aixplain_client...")
    from src.aixplain_client import AIXplainClient
    print("   ✓ AIXplain client loaded")

    print("6. Testing rule_extractor...")
    from src.rule_extractor import RuleExtractor, RuleMapper
    print("   ✓ Rule extractor loaded")

    print("7. Testing gap_analyzer...")
    from src.gap_analyzer import GapAnalyzer, CoverageAnalyzer
    print("   ✓ Gap analyzer loaded")

    print("8. Testing validation...")
    from src.validation import ValidationManager, AuditTrail
    print("   ✓ Validation loaded")

    print("9. Testing agent...")
    from src.agent import FinancialRulesAgent
    print("   ✓ Agent loaded")

    print("\n" + "=" * 60)
    print("✅ All imports successful!")
    print("=" * 60)
    print("\nThe application is ready to use!")
    print("\nNext steps:")
    print("  1. Set AIXPLAIN_API_KEY in .env file")
    print("  2. Run: streamlit run app.py")
    print("  3. Or run: python cli.py --help")

except ImportError as e:
    print(f"\n❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
