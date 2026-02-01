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

# Try to import new features (they may not exist yet)
try:
    from src.tracks_api import TracksAPI
    TRACKS_API_AVAILABLE = True
except ImportError:
    TRACKS_API_AVAILABLE = False

try:
    from src.integrations import NotificationManager
    INTEGRATIONS_AVAILABLE = True
except ImportError:
    INTEGRATIONS_AVAILABLE = False

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
        
        # Build navigation options
        nav_options = ["Extract Rules", "View Tracks", "Batch Processing", "Results History"]
        
        # Add optional pages if features available
        if TRACKS_API_AVAILABLE:
            nav_options.insert(2, "Manage Tracks")
        
        if INTEGRATIONS_AVAILABLE:
            nav_options.append("Integrations")
        
        page = st.radio(
            "Select Page",
            nav_options,
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
    elif page == "Manage Tracks":
        show_manage_tracks_page()
    elif page == "Batch Processing":
        show_batch_page()
    elif page == "Results History":
        show_history_page()
    elif page == "Integrations":
        show_integrations_page()


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


def show_manage_tracks_page():
    """Show track management page (NEW)."""
    st.header("🎛️ Track Management")
    
    if not TRACKS_API_AVAILABLE:
        st.error("❌ TracksAPI module not available. Please ensure src/tracks_api.py exists.")
        st.info("This feature allows dynamic management of financial tracks and rules.")
        return
    
    # Initialize TracksAPI
    tracks_api = TracksAPI()
    tracks_list = tracks_api.get_all_tracks()  # Returns list of FinancialTrack objects
    
    # Convert to dictionary for easier access (using track_id attribute)
    tracks = {track.track_id: track for track in tracks_list}
    
    st.info("💡 **Dynamic Track Management** - Add, edit, or remove rules without code changes!")
    
    # Add new rule section
    with st.expander("➕ Add New Rule to Track", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            track_id = st.selectbox(
                "Select Track",
                options=list(tracks.keys()),
                format_func=lambda x: f"{tracks[x].name_ar} ({tracks[x].name_en})"
            )
        
        with col2:
            rule_id = st.text_input("Rule ID", placeholder="e.g., CONTRACT_NEW_001")
        
        rule_desc_ar = st.text_area("Rule Description (Arabic)", placeholder="وصف القاعدة...")
        rule_desc_en = st.text_area("Rule Description (English)", placeholder="Rule description...")
        
        if st.button("➕ Add Rule", type="primary"):
            if rule_id and rule_desc_ar:
                try:
                    # TracksAPI expects text strings, not TrackRule objects
                    tracks_api.add_track_rule(track_id, rule_desc_ar, rule_desc_en)
                    st.success(f"✅ Rule '{rule_id}' added to {tracks[track_id].name_ar}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to add rule: {str(e)}")
            else:
                st.warning("⚠️ Please fill in Rule ID and Arabic Description")
    
    st.divider()
    
    # Display current tracks and rules
    st.subheader("📋 Current Tracks & Rules")
    
    for track in tracks_list:
        with st.expander(f"**{track.name_ar}** ({track.name_en}) - {len(track.current_rules)} rules", expanded=False):
            st.write(f"**Definition:** {track.definition_ar}")
            
            if track.current_rules:
                for idx, rule in enumerate(track.current_rules):
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.text(f"🔹 [{rule.rule_id}] {rule.description[:100]}{'...' if len(rule.description) > 100 else ''}")
                    
                    with col2:
                        if st.button("🗑️ Remove", key=f"remove_{track.track_id}_{idx}"):
                            try:
                                tracks_api.remove_track_rule(track.track_id, rule.rule_id)
                                st.success(f"✅ Removed rule '{rule.rule_id}'")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
            else:
                st.info("No rules defined for this track yet.")
    
    # Export/Import section
    st.divider()
    st.subheader("💾 Import / Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Export Tracks**")
        try:
            # Generate export data directly for UI download
            export_data = {
                "version": "1.0.0",
                "exported_at": datetime.now().isoformat(),
                "tracks": {
                    track.track_id: {
                        "name_ar": track.name_ar,
                        "name_en": track.name_en,
                        "definition_ar": track.definition_ar,
                        "definition_en": track.definition_en,
                        "rules": [
                            {
                                "rule_id": rule.rule_id,
                                "description": rule.description,
                                "source": rule.source
                            }
                            for rule in track.current_rules
                        ]
                    }
                    for track in tracks_list
                }
            }
            
            tracks_json = json.dumps(export_data, ensure_ascii=False, indent=2)
            
            st.download_button(
                label="📥 Download tracks.json",
                data=tracks_json,
                file_name=f"tracks_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        except Exception as e:
            st.error(f"Export failed: {str(e)}")
    
    with col2:
        st.write("**Import Tracks**")
        import_file = st.file_uploader("Upload tracks.json", type=['json'], key="import_tracks")
        if import_file:
            if st.button("📤 Import"):
                try:
                    tracks_api.import_tracks(import_file.getvalue().decode('utf-8'))
                    st.success("✅ Tracks imported successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Import failed: {str(e)}")
    
    # Statistics
    st.divider()
    st.subheader("📊 Statistics")
    
    try:
        stats = tracks_api.get_statistics()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Tracks", stats.get('total_tracks', len(tracks_list)))
        col2.metric("Total Rules", stats.get('total_rules', sum(len(t.current_rules) for t in tracks_list)))
        col3.metric("Version", stats.get('version', '1.0.0'))
        col4.metric("Last Updated", stats.get('last_updated', 'Never')[:10] if stats.get('last_updated') else "Never")
    except Exception as e:
        st.error(f"Failed to load statistics: {str(e)}")
        # Fallback statistics
        col1, col2 = st.columns(2)
        col1.metric("Total Tracks", len(tracks_list))
        col2.metric("Total Rules", sum(len(t.current_rules) for t in tracks_list))


def show_integrations_page():
    """Show integrations configuration page (NEW)."""
    st.header("🔌 External Integrations")
    
    if not INTEGRATIONS_AVAILABLE:
        st.error("❌ Integrations module not available. Please ensure src/integrations.py exists.")
        st.info("This feature enables Slack, Discord, Email, and Webhook notifications.")
        return
    
    st.info("💡 **External Notifications** - Get notified when rule extraction completes!")
    
    # Configuration tabs
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Slack", "🎮 Discord", "📧 Email", "🌐 Webhooks"])
    
    with tab1:
        st.subheader("Slack Integration")
        st.write("Send notifications to Slack channels via incoming webhooks.")
        
        slack_enabled = st.checkbox("Enable Slack Notifications", value=False)
        slack_webhook = st.text_input(
            "Slack Webhook URL",
            type="password",
            placeholder="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
            help="Get this from Slack's Incoming Webhooks app"
        )
        slack_channel = st.text_input("Channel (optional)", placeholder="#financial-rules")
        
        if slack_enabled and slack_webhook:
            if st.button("🧪 Test Slack Notification"):
                try:
                    from src.integrations import SlackIntegration
                    slack = SlackIntegration(slack_webhook, slack_channel)
                    success = slack.send_notification(
                        title="Test Notification",
                        message="This is a test from Financial Rules Agent!",
                        status="success"
                    )
                    if success:
                        st.success("✅ Slack notification sent successfully!")
                    else:
                        st.error("❌ Failed to send notification. Check your webhook URL.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        st.code(f"""# Add to .env file:
SLACK_WEBHOOK_URL={slack_webhook if slack_webhook else 'your-webhook-url'}
SLACK_CHANNEL={slack_channel if slack_channel else '#channel-name'}
ENABLE_NOTIFICATIONS=true""", language="bash")
    
    with tab2:
        st.subheader("Discord Integration")
        st.write("Send rich embeds to Discord channels via webhooks.")
        
        discord_enabled = st.checkbox("Enable Discord Notifications", value=False)
        discord_webhook = st.text_input(
            "Discord Webhook URL",
            type="password",
            placeholder="https://discord.com/api/webhooks/YOUR/WEBHOOK",
            help="Create a webhook in your Discord server settings"
        )
        
        if discord_enabled and discord_webhook:
            if st.button("🧪 Test Discord Notification"):
                try:
                    from src.integrations import DiscordIntegration
                    discord = DiscordIntegration(discord_webhook)
                    success = discord.send_notification(
                        title="Test Notification",
                        message="This is a test from Financial Rules Agent!",
                        status="success"
                    )
                    if success:
                        st.success("✅ Discord notification sent successfully!")
                    else:
                        st.error("❌ Failed to send notification. Check your webhook URL.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        st.code(f"""# Add to .env file:
DISCORD_WEBHOOK_URL={discord_webhook if discord_webhook else 'your-webhook-url'}
ENABLE_NOTIFICATIONS=true""", language="bash")
    
    with tab3:
        st.subheader("Email Integration")
        st.write("Send email notifications via SMTP.")
        
        email_enabled = st.checkbox("Enable Email Notifications", value=False)
        
        col1, col2 = st.columns(2)
        with col1:
            smtp_host = st.text_input("SMTP Host", placeholder="smtp.gmail.com")
            smtp_user = st.text_input("SMTP Username", placeholder="your@email.com")
            smtp_from = st.text_input("From Email", placeholder="noreply@example.com")
        
        with col2:
            smtp_port = st.number_input("SMTP Port", value=587, min_value=1, max_value=65535)
            smtp_password = st.text_input("SMTP Password", type="password")
            notification_email = st.text_input("Send To", placeholder="recipient@example.com")
        
        if email_enabled and all([smtp_host, smtp_user, smtp_password, notification_email]):
            if st.button("🧪 Test Email Notification"):
                st.info("Email testing requires async execution. Add credentials to .env and test via CLI.")
        
        st.code(f"""# Add to .env file:
SMTP_HOST={smtp_host if smtp_host else 'smtp.gmail.com'}
SMTP_PORT={smtp_port}
SMTP_USER={smtp_user if smtp_user else 'your@email.com'}
SMTP_PASSWORD=your-password
SMTP_FROM={smtp_from if smtp_from else 'noreply@example.com'}
NOTIFICATION_EMAIL={notification_email if notification_email else 'recipient@example.com'}
ENABLE_NOTIFICATIONS=true""", language="bash")
    
    with tab4:
        st.subheader("Custom Webhook Integration")
        st.write("Send notifications to any custom webhook endpoint.")
        
        webhook_enabled = st.checkbox("Enable Webhook Notifications", value=False)
        webhook_url = st.text_input(
            "Webhook URL",
            placeholder="https://your-api.com/webhook"
        )
        webhook_method = st.selectbox("HTTP Method", ["POST", "PUT"], index=0)
        
        if webhook_enabled and webhook_url:
            if st.button("🧪 Test Webhook"):
                try:
                    from src.integrations import WebhookIntegration
                    webhook = WebhookIntegration(webhook_url, method=webhook_method)
                    success = webhook.send_notification(
                        title="Test Notification",
                        message="This is a test from Financial Rules Agent!",
                        status="success"
                    )
                    if success:
                        st.success("✅ Webhook notification sent successfully!")
                    else:
                        st.error("❌ Failed to send notification. Check your webhook URL.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        st.code(f"""# Add to .env file:
CUSTOM_WEBHOOK_URL={webhook_url if webhook_url else 'https://your-api.com/webhook'}
WEBHOOK_METHOD={webhook_method}
ENABLE_NOTIFICATIONS=true""", language="bash")
    
    # Current configuration
    st.divider()
    st.subheader("📋 Current Configuration")
    
    st.info(f"""
    **Configuration File:** `.env`
    
    To enable integrations:
    1. Copy settings from tabs above to your `.env` file
    2. Set `ENABLE_NOTIFICATIONS=true`
    3. Restart the application
    4. Notifications will be sent automatically after each extraction
    """)




if __name__ == "__main__":
    main()
