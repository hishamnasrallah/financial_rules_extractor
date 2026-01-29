"""
Streamlit web application for the Financial Rules Extraction Agent.
"""
import json
from datetime import datetime
from pathlib import Path
import time

import streamlit as st
import pandas as pd
from loguru import logger

from src.agent import FinancialRulesAgent
from src.models import DocumentType
from src.tracks import TracksRepository
from src.config import config

# Page configuration
st.set_page_config(
    page_title="Financial Rules Extractor",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .stAlert {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    if 'results' not in st.session_state:
        st.session_state.results = []
    if 'current_result' not in st.session_state:
        st.session_state.current_result = None


def initialize_agent(api_key: str):
    """Initialize the agent with API key."""
    try:
        agent = FinancialRulesAgent(api_key=api_key)
        st.session_state.agent = agent
        # Show warning if models couldn't be loaded
        if not agent.client.search_model and not agent.client.llm_model:
            st.warning("⚠️ Could not load aiXplain models. System will use pattern-based extraction (offline mode).")
        return True
    except Exception as e:
        st.error(f"Failed to initialize agent: {str(e)}")
        return False


def main():
    """Main application."""
    init_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">📋 Financial Rules Extraction Agent</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Powered by aiXplain - Extract and analyze financial rules from official documents</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input
        api_key = st.text_input(
            "aiXplain API Key",
            type="password",
            value=config.aixplain.api_key if config.aixplain.api_key else "",
            help="Enter your aiXplain API key"
        )
        
        if api_key and not st.session_state.agent:
            if st.button("Initialize Agent", type="primary"):
                with st.spinner("Initializing agent..."):
                    if initialize_agent(api_key):
                        st.success("✅ Agent initialized successfully!")
        
        if st.session_state.agent:
            st.success("✅ Agent ready")
        
        st.divider()
        
        # Navigation
        st.header("📑 Navigation")
        page = st.radio(
            "Select Page",
            ["Extract Rules", "View Tracks", "Batch Processing", "Results History"],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # About
        with st.expander("ℹ️ About"):
            st.markdown("""
            **Financial Rules Extraction Agent**
            
            This agent analyzes official documents and extracts financial rules,
            mapping them to predefined tracks:
            - 🏗️ Contracts (العقود)
            - 💰 Salaries (الرواتب)
            - 🧾 Invoices (الفواتير)
            
            **Features:**
            - Document parsing (PDF, Web pages)
            - Rule extraction using AI
            - Gap analysis
            - HITL validation support
            """)
    
    # Main content based on selected page
    if page == "Extract Rules":
        show_extract_page()
    elif page == "View Tracks":
        show_tracks_page()
    elif page == "Batch Processing":
        show_batch_page()
    elif page == "Results History":
        show_history_page()


def show_extract_page():
    """Show the rule extraction page."""
    st.header("📄 Extract Rules from Document")
    
    if not st.session_state.agent:
        st.warning("⚠️ Please initialize the agent first by entering your API key in the sidebar.")
        return
    
    # Document input
    col1, col2 = st.columns([2, 1])
    
    with col1:
        doc_name = st.text_input("Document Name", placeholder="e.g., نظام الخدمة المدنية")
    
    with col2:
        doc_type = st.selectbox(
            "Document Type",
            ["Auto-detect", "PDF", "Web Page", "Text"],
            index=0
        )
    
    # Input method tabs
    tab1, tab2 = st.tabs(["📎 URL", "📁 Upload File"])
    
    doc_url = None
    uploaded_file = None
    
    with tab1:
        doc_url = st.text_input(
            "Document URL",
            placeholder="https://example.com/document.pdf"
        )
    
    with tab2:
        uploaded_file = st.file_uploader(
            "Upload Document",
            type=['pdf', 'txt'],
            help="Upload a PDF or text file"
        )
    
    # Extract button
    if st.button("🚀 Extract Rules", type="primary", disabled=not doc_name):
        if not doc_url and not uploaded_file:
            st.error("Please provide either a URL or upload a file.")
            return
        
        # Save uploaded file temporarily
        file_path = None
        if uploaded_file:
            temp_dir = Path(config.app.data_dir) / "temp"
            temp_dir.mkdir(exist_ok=True)
            file_path = temp_dir / uploaded_file.name
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
        
        # Process document
        with st.spinner("Processing document... This may take a minute."):
            try:
                # Determine document type
                document_type = None
                if doc_type != "Auto-detect":
                    type_map = {
                        "PDF": DocumentType.PDF,
                        "Web Page": DocumentType.WEB_PAGE,
                        "Text": DocumentType.TEXT
                    }
                    document_type = type_map[doc_type]
                
                result = st.session_state.agent.process_document(
                    name=doc_name,
                    url=doc_url if doc_url else None,
                    file_path=str(file_path) if file_path else None,
                    document_type=document_type
                )
                
                st.session_state.current_result = result
                st.session_state.results.append(result)
                
                st.success(f"✅ Processing completed in {result.processing_time_seconds:.2f} seconds!")
                
                # Display results
                display_extraction_result(result)
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                logger.exception("Extraction failed")


def display_extraction_result(result):
    """Display extraction result."""
    st.divider()
    st.subheader("📊 Extraction Results")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Rules", result.statistics['total_rules'])
    
    with col2:
        st.metric("Gaps Identified", result.statistics['total_gaps'])
    
    with col3:
        st.metric("Avg Confidence", f"{result.statistics['average_mapping_confidence']:.2f}")
    
    with col4:
        st.metric("Processing Time", f"{result.processing_time_seconds:.1f}s")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Extracted Rules", "⚠️ Gaps", "📈 Statistics", "💾 Export"])
    
    with tab1:
        st.subheader("Extracted Rules")
        
        if result.extracted_rules:
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                track_filter = st.multiselect(
                    "Filter by Track",
                    options=['contracts', 'salaries', 'invoices', 'unmapped'],
                    default=['contracts', 'salaries', 'invoices', 'unmapped']
                )
            
            with col2:
                status_filter = st.multiselect(
                    "Filter by Status",
                    options=['extracted', 'mapped', 'requires_review'],
                    default=['extracted', 'mapped', 'requires_review']
                )
            
            # Filter rules
            filtered_rules = [
                r for r in result.extracted_rules
                if (r.track_id in track_filter or (r.track_id is None and 'unmapped' in track_filter))
                and r.status.value in status_filter
            ]
            
            # Display as table
            if filtered_rules:
                rules_data = []
                for rule in filtered_rules:
                    rules_data.append({
                        'Rule ID': rule.rule_id,
                        'Text': rule.text_ar[:100] + '...' if len(rule.text_ar) > 100 else rule.text_ar,
                        'Track': rule.track_id or 'Unmapped',
                        'Confidence': f"{rule.mapping_confidence:.2f}",
                        'Status': rule.status.value,
                        'Source': rule.source_reference.document_name
                    })
                
                df = pd.DataFrame(rules_data)
                st.dataframe(df, use_container_width=True, height=400)
            else:
                st.info("No rules match the selected filters.")
        else:
            st.info("No rules were extracted from this document.")
    
    with tab2:
        st.subheader("Identified Gaps")
        
        if result.gaps:
            # Gap summary
            gaps_by_severity = {}
            for gap in result.gaps:
                severity = gap.severity
                gaps_by_severity[severity] = gaps_by_severity.get(severity, 0) + 1
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("High Severity", gaps_by_severity.get('high', 0))
            with col2:
                st.metric("Medium Severity", gaps_by_severity.get('medium', 0))
            with col3:
                st.metric("Low Severity", gaps_by_severity.get('low', 0))
            
            # Display gaps
            for gap in result.gaps:
                with st.expander(f"🔴 {gap.gap_type.upper()} - {gap.track_id}"):
                    st.write(f"**Rule:** {gap.extracted_rule.text_ar}")
                    st.write(f"**Severity:** {gap.severity}")
                    st.write(f"**Recommendation:** {gap.recommendation}")
                    if gap.similar_existing_rules:
                        st.write(f"**Similar Rules:** {', '.join(gap.similar_existing_rules)}")
        else:
            st.success("✅ No gaps identified! All extracted rules align with existing coverage.")
    
    with tab3:
        st.subheader("Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Rules by Track**")
            track_df = pd.DataFrame([
                {'Track': k, 'Count': v}
                for k, v in result.statistics['rules_by_track'].items()
            ])
            st.bar_chart(track_df.set_index('Track'))
        
        with col2:
            st.write("**Rules by Status**")
            status_df = pd.DataFrame([
                {'Status': k, 'Count': v}
                for k, v in result.statistics['rules_by_status'].items()
            ])
            st.bar_chart(status_df.set_index('Status'))
    
    with tab4:
        st.subheader("Export Results")
        
        # Convert to JSON
        result_dict = {
            'document_id': result.document_id,
            'extracted_rules': [
                {
                    'rule_id': r.rule_id,
                    'text_ar': r.text_ar,
                    'track_id': r.track_id,
                    'status': r.status.value,
                    'mapping_confidence': r.mapping_confidence,
                }
                for r in result.extracted_rules
            ],
            'gaps': [
                {
                    'gap_id': g.gap_id,
                    'track_id': g.track_id,
                    'gap_type': g.gap_type,
                    'severity': g.severity,
                    'recommendation': g.recommendation
                }
                for g in result.gaps
            ],
            'statistics': result.statistics
        }
        
        json_str = json.dumps(result_dict, ensure_ascii=False, indent=2)
        
        st.download_button(
            label="📥 Download as JSON",
            data=json_str,
            file_name=f"extraction_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )


def show_tracks_page():
    """Show the financial tracks page."""
    st.header("🎯 Financial Tracks")
    
    tracks = TracksRepository.get_all_tracks()
    
    for track_id, track in tracks.items():
        with st.expander(f"**{track.name_ar}** ({track.name_en})", expanded=True):
            st.write(f"**Definition:** {track.definition_ar}")
            st.write(f"**Current Rules:** {len(track.current_rules)}")
            
            if track.current_rules:
                rules_data = []
                for rule in track.current_rules:
                    rules_data.append({
                        'Rule ID': rule.rule_id,
                        'Description': rule.description
                    })
                
                df = pd.DataFrame(rules_data)
                st.dataframe(df, use_container_width=True)


def show_batch_page():
    """Show the batch processing page."""
    st.header("📦 Batch Processing")
    
    if not st.session_state.agent:
        st.warning("⚠️ Please initialize the agent first by entering your API key in the sidebar.")
        return
    
    st.info("Upload a JSON configuration file with multiple documents to process them in batch.")
    
    # Example config
    with st.expander("📄 View Example Configuration"):
        example_config = [
            {
                "name": "نظام الخدمة المدنية",
                "url": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/5fb85c90-8962-402d-b2e7-a9a700f2ad95/1",
                "type": "web_page"
            },
            {
                "name": "نظام وظائف مباشرة الأموال العامة",
                "url": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/b8f2e25e-7f48-40e6-a581-a9a700f551bb/1",
                "type": "web_page"
            }
        ]
        st.json(example_config)
    
    # Upload config file
    config_file = st.file_uploader("Upload Configuration (JSON)", type=['json'])
    
    if config_file:
        try:
            documents = json.load(config_file)
            st.success(f"✅ Loaded {len(documents)} documents")
            
            if st.button("🚀 Process Batch", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                results = []
                for idx, doc in enumerate(documents):
                    status_text.text(f"Processing {idx + 1}/{len(documents)}: {doc['name']}")
                    progress_bar.progress((idx + 1) / len(documents))
                    
                    try:
                        result = st.session_state.agent.process_document(
                            name=doc['name'],
                            url=doc.get('url'),
                            file_path=doc.get('file_path'),
                            document_type=DocumentType[doc['type'].upper()] if doc.get('type') else None
                        )
                        results.append(result)
                    except Exception as e:
                        st.error(f"Failed to process {doc['name']}: {str(e)}")
                
                # Generate comprehensive report
                if results:
                    report = st.session_state.agent.generate_comprehensive_report(results)
                    
                    st.success("✅ Batch processing completed!")
                    
                    # Display report
                    display_batch_report(report)
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


def display_batch_report(report):
    """Display batch processing report."""
    st.divider()
    st.subheader("📊 Comprehensive Report")
    
    # Summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Documents", report['metadata']['num_documents_processed'])
    with col2:
        st.metric("Total Rules", report['summary']['total_rules_extracted'])
    with col3:
        st.metric("Total Gaps", report['summary']['total_gaps_identified'])
    with col4:
        st.metric("Processing Time", f"{report['metadata']['total_processing_time_seconds']:.1f}s")
    
    # Coverage by track
    st.subheader("Coverage Analysis")
    coverage_data = []
    for track_id, coverage in report['coverage_analysis']['by_track'].items():
        coverage_data.append({
            'Track': coverage['track_name'],
            'Existing Rules': coverage['existing_rules'],
            'Extracted Rules': coverage['extracted_rules'],
            'Gaps': coverage['identified_gaps'],
            'Coverage %': coverage['coverage_percentage']
        })
    
    df = pd.DataFrame(coverage_data)
    st.dataframe(df, use_container_width=True)


def show_history_page():
    """Show results history."""
    st.header("📜 Results History")
    
    if not st.session_state.results:
        st.info("No results yet. Process some documents to see them here.")
        return
    
    for idx, result in enumerate(reversed(st.session_state.results)):
        with st.expander(f"Result {len(st.session_state.results) - idx}: {result.document_id}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rules", result.statistics['total_rules'])
            with col2:
                st.metric("Gaps", result.statistics['total_gaps'])
            with col3:
                st.metric("Time", f"{result.processing_time_seconds:.1f}s")
            
            if st.button(f"View Details", key=f"view_{idx}"):
                st.session_state.current_result = result
                display_extraction_result(result)


if __name__ == "__main__":
    main()
