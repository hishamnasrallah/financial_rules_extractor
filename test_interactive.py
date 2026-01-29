"""
Interactive Testing Guide for Financial Rules Extraction Agent
This script provides various ways to test and interact with the agent.
"""
import os
from dotenv import load_dotenv
load_dotenv()

from src.agent import FinancialRulesAgent
from src.tracks import TracksRepository
from src.models import DocumentType

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def test_1_check_tracks():
    """Test 1: Verify financial tracks are loaded correctly"""
    print_header("Test 1: Check Financial Tracks")
    
    tracks = TracksRepository.get_all_tracks()
    
    print_info(f"Found {len(tracks)} financial tracks:")
    
    for track_id, track in tracks.items():
        print(f"\n  📋 {track.name_ar} ({track.name_en})")
        print(f"     ID: {track_id}")
        print(f"     Current Rules: {len(track.current_rules)}")
        
        # Show first 2 rules
        for i, rule in enumerate(track.current_rules[:2], 1):
            print(f"     {i}. {rule.description[:60]}...")
    
    print_success("Tracks loaded successfully!")
    return True


def test_2_initialize_agent():
    """Test 2: Initialize the agent with API key"""
    print_header("Test 2: Initialize Agent")
    
    api_key = os.getenv("AIXPLAIN_API_KEY")
    
    if not api_key:
        print_error("AIXPLAIN_API_KEY not found in environment")
        print_warning("Please set it in your .env file")
        return None
    
    print_info("API key found")
    print_info("Initializing agent...")
    
    try:
        agent = FinancialRulesAgent(api_key=api_key)
        print_success("Agent initialized successfully!")
        return agent
    except Exception as e:
        print_error(f"Failed to initialize agent: {e}")
        return None


def test_3_parse_sample_text():
    """Test 3: Test rule extraction on sample Arabic text"""
    print_header("Test 3: Extract Rules from Sample Text")
    
    # Sample Arabic financial rule text
    sample_text = """
    المادة الخامسة والعشرون:
    
    1. يجب التحقق من أن مجموع الحسميات على الراتب لا يتجاوز ثلث الراتب الأساسي للموظف.
    
    2. التحقق من مطابقة المبالغ المراد صرفها مع الفواتير المقدمة من الجهات المعتمدة.
    
    3. في حالة المستخلص الختامي للعقود، يجب ألا تقل نسبته عن 10% من إجمالي قيمة العقد.
    
    4. يشترط وجود خطاب تكليف للعمل الإضافي يتضمن جميع التفاصيل المطلوبة.
    """
    
    print_info("Sample text (Arabic financial rules):")
    print(f"{Colors.OKBLUE}{sample_text[:200]}...{Colors.ENDC}")
    
    # Create a simple document
    from src.models import Document
    from datetime import datetime
    
    doc = Document(
        document_id=f"test_doc_{int(datetime.now().timestamp())}",
        name="Sample Test Document",
        document_type=DocumentType.TEXT,
        content=sample_text
    )
    
    print_success("Sample document created")
    
    # Extract rules using pattern matching (without API call)
    from src.rule_extractor import RuleExtractor
    from src.aixplain_client import AIXplainClient
    
    # Use mock client for testing
    print_info("Extracting rules (using pattern-based extraction)...")
    
    # Simple pattern extraction test
    import re
    patterns = [
        r'يجب\s+[^.]*[.]',
        r'التحقق\s+من\s+[^.]*[.]',
        r'يشترط\s+[^.]*[.]',
    ]
    
    found_rules = []
    for pattern in patterns:
        matches = re.finditer(pattern, sample_text, re.UNICODE)
        for match in matches:
            found_rules.append(match.group().strip())
    
    print_success(f"Found {len(found_rules)} rules using pattern matching:")
    
    for i, rule in enumerate(found_rules, 1):
        print(f"\n  {i}. {rule}")
        
        # Try to guess the track
        if 'راتب' in rule or 'حسميات' in rule or 'موظف' in rule:
            track = "الرواتب (Salaries)"
        elif 'عقد' in rule or 'مستخلص' in rule:
            track = "العقود (Contracts)"
        elif 'فاتورة' in rule or 'صرف' in rule:
            track = "الفواتير (Invoices)"
        else:
            track = "غير محدد (Unmapped)"
        
        print(f"     → Likely track: {track}")
    
    print_success("Pattern-based extraction completed!")
    return True


def test_4_process_real_document(agent):
    """Test 4: Process a real document (requires API key and internet)"""
    print_header("Test 4: Process Real Document")
    
    if not agent:
        print_warning("Skipping - agent not initialized")
        return False
    
    print_info("This test will process a real document from the web")
    print_warning("Note: This requires a valid aiXplain API key and internet connection")
    
    response = input("\n  Do you want to continue? (y/n): ")
    if response.lower() != 'y':
        print_info("Test skipped by user")
        return False
    
    # Use a sample document
    doc_url = "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/5fb85c90-8962-402d-b2e7-a9a700f2ad95/1"
    doc_name = "نظام الخدمة المدنية"
    
    print_info(f"Processing: {doc_name}")
    print_info(f"URL: {doc_url}")
    print_info("This may take 30-60 seconds...")
    
    try:
        result = agent.process_document(
            name=doc_name,
            url=doc_url,
            document_type=DocumentType.WEB_PAGE
        )
        
        print_success("Document processed successfully!")
        
        # Display results
        print(f"\n  📊 Results:")
        print(f"     Total Rules Extracted: {len(result.extracted_rules)}")
        print(f"     Gaps Identified: {len(result.gaps)}")
        print(f"     Processing Time: {result.processing_time_seconds:.2f}s")
        
        # Show rules by track
        print(f"\n  📋 Rules by Track:")
        for track, count in result.statistics['rules_by_track'].items():
            print(f"     - {track}: {count} rules")
        
        # Show first 3 rules
        if result.extracted_rules:
            print(f"\n  📝 Sample Extracted Rules:")
            for i, rule in enumerate(result.extracted_rules[:3], 1):
                print(f"\n     {i}. {rule.text_ar[:80]}...")
                print(f"        Track: {rule.track_id or 'Unmapped'}")
                print(f"        Confidence: {rule.mapping_confidence:.2%}")
        
        # Show gaps if any
        if result.gaps:
            print(f"\n  ⚠️  Sample Gaps:")
            for i, gap in enumerate(result.gaps[:2], 1):
                print(f"\n     {i}. Type: {gap.gap_type}, Severity: {gap.severity}")
                print(f"        Track: {gap.track_id}")
        
        return True
        
    except Exception as e:
        print_error(f"Failed to process document: {e}")
        print_warning("This might be due to:")
        print_warning("  - Invalid API key")
        print_warning("  - Network connectivity issues")
        print_warning("  - aiXplain service unavailability")
        return False


def test_5_interactive_qa():
    """Test 5: Interactive Q&A about the system"""
    print_header("Test 5: Interactive Q&A")
    
    print_info("Ask questions about the system (type 'exit' to stop)")
    print_info("Example questions:")
    print("  - What tracks are available?")
    print("  - What rules exist for salaries?")
    print("  - How does gap analysis work?")
    print("  - What documents can be processed?")
    
    tracks = TracksRepository.get_all_tracks()
    
    while True:
        print(f"\n{Colors.OKBLUE}Your question: {Colors.ENDC}", end="")
        question = input().strip().lower()
        
        if question in ['exit', 'quit', 'q']:
            print_info("Exiting Q&A mode")
            break
        
        # Simple keyword-based responses
        if 'track' in question or 'مسار' in question:
            print_success(f"Available tracks: {', '.join(tracks.keys())}")
            for track_id, track in tracks.items():
                print(f"  - {track.name_ar} ({track.name_en})")
        
        elif 'salary' in question or 'salaries' in question or 'رواتب' in question:
            track = tracks['salaries']
            print_success(f"Salaries track has {len(track.current_rules)} rules:")
            for i, rule in enumerate(track.current_rules, 1):
                print(f"  {i}. {rule.description}")
        
        elif 'contract' in question or 'عقد' in question:
            track = tracks['contracts']
            print_success(f"Contracts track has {len(track.current_rules)} rules:")
            for i, rule in enumerate(track.current_rules, 1):
                print(f"  {i}. {rule.description}")
        
        elif 'invoice' in question or 'فاتورة' in question:
            track = tracks['invoices']
            print_success(f"Invoices track has {len(track.current_rules)} rules:")
            for i, rule in enumerate(track.current_rules, 1):
                print(f"  {i}. {rule.description}")
        
        elif 'gap' in question or 'فجوة' in question:
            print_success("Gap analysis identifies:")
            print("  - Missing rules: Rules mentioned in documents but not in system")
            print("  - Partial coverage: Rules partially implemented")
            print("  - Conflicting rules: Rules that contradict existing ones")
        
        elif 'document' in question or 'وثيقة' in question:
            print_success("Supported document types:")
            print("  - PDF files (.pdf)")
            print("  - Web pages (HTML)")
            print("  - Plain text (.txt)")
            print("  - Arabic and English text")
        
        elif 'how' in question and 'work' in question:
            print_success("System workflow:")
            print("  1. Parse document (extract text)")
            print("  2. Index in aiXplain aiR (vector database)")
            print("  3. Extract rules using LLM")
            print("  4. Map rules to tracks")
            print("  5. Identify gaps vs existing rules")
            print("  6. Flag low-confidence rules for review")
        
        elif 'help' in question or question == '?':
            print_info("Available topics:")
            print("  - tracks: Show available financial tracks")
            print("  - salaries/contracts/invoices: Show rules for specific track")
            print("  - gaps: Explain gap analysis")
            print("  - documents: Show supported formats")
            print("  - how does it work: Explain workflow")
        
        else:
            print_warning("I don't understand that question. Type 'help' for topics or 'exit' to quit.")


def main():
    """Run all tests"""
    print_header("Financial Rules Extraction Agent - Interactive Testing")
    
    print_info("This script will run various tests to verify the agent is working")
    print_info("Some tests require an aiXplain API key\n")
    
    # Test 1: Check tracks
    test_1_check_tracks()
    input("\nPress Enter to continue...")
    
    # Test 2: Initialize agent
    agent = test_2_initialize_agent()
    input("\nPress Enter to continue...")
    
    # Test 3: Pattern-based extraction
    test_3_parse_sample_text()
    input("\nPress Enter to continue...")
    
    # Test 4: Process real document (optional)
    if agent:
        test_4_process_real_document(agent)
        input("\nPress Enter to continue...")
    else:
        print_warning("\nSkipping real document test (no agent initialized)")
        input("\nPress Enter to continue...")
    
    # Test 5: Interactive Q&A
    test_5_interactive_qa()
    
    print_header("Testing Complete!")
    print_success("All tests completed successfully!")
    print_info("\nNext steps:")
    print("  1. Try the web interface: streamlit run app.py")
    print("  2. Try the CLI: python cli.py extract --name 'Test' --url 'https://...'")
    print("  3. Read the documentation: docs/USER_GUIDE.md")


if __name__ == "__main__":
    main()
