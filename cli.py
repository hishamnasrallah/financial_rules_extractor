"""
Command-line interface for the Financial Rules Extraction Agent.
"""
import sys
import json
from pathlib import Path
from typing import Optional

import click
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.agent import FinancialRulesAgent
from src.models import DocumentType
from src.config import config
from src.tracks import TracksRepository

console = Console()


# Configure logger
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level=config.app.log_level
)
logger.add(
    config.app.logs_dir / "agent_{time}.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG"
)


@click.group()
@click.version_option(version="1.0.0", prog_name="Financial Rules Extractor")
def cli():
    """
    Financial Rules Extraction Agent CLI
    
    Extract and analyze financial rules from official documents using aiXplain.
    """
    pass


@cli.command()
@click.option('--name', '-n', required=True, help='Document name')
@click.option('--url', '-u', help='Document URL (for PDF or web page)')
@click.option('--file', '-f', 'file_path', type=click.Path(exists=True), help='Local file path')
@click.option('--type', '-t', 'doc_type', 
              type=click.Choice(['pdf', 'web_page', 'text'], case_sensitive=False),
              help='Document type (auto-detected if not specified)')
@click.option('--output', '-o', type=click.Path(), help='Output file path for results (JSON)')
@click.option('--api-key', envvar='AIXPLAIN_API_KEY', help='aiXplain API key')
def extract(name: str, url: Optional[str], file_path: Optional[str], 
            doc_type: Optional[str], output: Optional[str], api_key: Optional[str]):
    """
    Extract rules from a single document.
    
    Example:
        extract-rules extract --name "نظام الخدمة المدنية" --url "https://example.com/doc.pdf"
    """
    console.print(Panel.fit(
        "[bold cyan]Financial Rules Extraction Agent[/bold cyan]\n"
        "Powered by aiXplain",
        box=box.DOUBLE
    ))
    
    if not url and not file_path:
        console.print("[red]Error:[/red] Either --url or --file must be provided")
        sys.exit(1)
    
    # Validate API key
    if not api_key:
        console.print("[red]Error:[/red] AIXPLAIN_API_KEY is required. Set it in .env or use --api-key")
        sys.exit(1)
    
    try:
        # Initialize agent
        console.print("\n[cyan]Initializing agent...[/cyan]")
        agent = FinancialRulesAgent(api_key=api_key)
        
        # Convert doc_type to enum
        document_type = DocumentType[doc_type.upper()] if doc_type else None
        
        # Process document
        console.print(f"\n[cyan]Processing document:[/cyan] {name}")
        with console.status("[bold green]Extracting rules..."):
            result = agent.process_document(
                name=name,
                url=url,
                file_path=file_path,
                document_type=document_type
            )
        
        # Display results
        _display_extraction_result(result)
        
        # Save to file if requested
        if output:
            _save_result_to_file(result, output)
            console.print(f"\n[green]✓[/green] Results saved to: {output}")
        
        console.print(f"\n[green]✓[/green] Processing completed in {result.processing_time_seconds:.2f} seconds")
        
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {str(e)}")
        logger.exception("Extraction failed")
        sys.exit(1)


@cli.command()
@click.option('--config-file', '-c', type=click.Path(exists=True), required=True,
              help='JSON config file with list of documents to process')
@click.option('--output', '-o', type=click.Path(), help='Output file path for comprehensive report (JSON)')
@click.option('--api-key', envvar='AIXPLAIN_API_KEY', help='aiXplain API key')
def batch(config_file: str, output: Optional[str], api_key: Optional[str]):
    """
    Process multiple documents in batch mode.
    
    Example:
        extract-rules batch --config-file documents.json --output report.json
    """
    console.print(Panel.fit(
        "[bold cyan]Financial Rules Extraction Agent - Batch Mode[/bold cyan]",
        box=box.DOUBLE
    ))
    
    # Validate API key
    if not api_key:
        console.print("[red]Error:[/red] AIXPLAIN_API_KEY is required")
        sys.exit(1)
    
    try:
        # Load config file
        with open(config_file, 'r', encoding='utf-8') as f:
            documents = json.load(f)
        
        console.print(f"\n[cyan]Loaded {len(documents)} documents from config[/cyan]")
        
        # Initialize agent
        console.print("[cyan]Initializing agent...[/cyan]")
        agent = FinancialRulesAgent(api_key=api_key)
        
        # Process documents
        console.print("\n[cyan]Processing documents...[/cyan]")
        results = agent.process_multiple_documents(documents)
        
        # Generate comprehensive report
        console.print("\n[cyan]Generating comprehensive report...[/cyan]")
        report = agent.generate_comprehensive_report(results)
        
        # Display summary
        _display_batch_summary(report)
        
        # Save report
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            console.print(f"\n[green]✓[/green] Report saved to: {output}")
        
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {str(e)}")
        logger.exception("Batch processing failed")
        sys.exit(1)


@cli.command()
def list_tracks():
    """List all available financial tracks."""
    console.print(Panel.fit(
        "[bold cyan]Financial Tracks[/bold cyan]",
        box=box.DOUBLE
    ))
    
    tracks = TracksRepository.get_all_tracks()
    
    for track_id, track in tracks.items():
        table = Table(title=f"{track.name_ar} ({track.name_en})", box=box.ROUNDED)
        table.add_column("Rule ID", style="cyan")
        table.add_column("Description", style="white")
        
        for rule in track.current_rules:
            table.add_row(rule.rule_id, rule.description)
        
        console.print(f"\n[bold]Definition:[/bold] {track.definition_ar}")
        console.print(table)


@cli.command()
@click.option('--output', '-o', type=click.Path(), default='config_example.json',
              help='Output file path for example config')
def init_config(output: str):
    """Generate an example configuration file for batch processing."""
    
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
        },
        {
            "name": "تعليمات تنفيذ الميزانية",
            "url": "https://www.mof.gov.sa/budget/Documents/budget_2023.pdf",
            "type": "pdf"
        }
    ]
    
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(example_config, f, ensure_ascii=False, indent=2)
    
    console.print(f"[green]✓[/green] Example config saved to: {output}")
    console.print("\nEdit this file with your documents and run:")
    console.print(f"  [cyan]extract-rules batch --config-file {output}[/cyan]")


def _display_extraction_result(result):
    """Display extraction result in a formatted way."""
    
    # Summary table
    summary_table = Table(title="Extraction Summary", box=box.ROUNDED)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Total Rules Extracted", str(result.statistics['total_rules']))
    summary_table.add_row("Total Gaps Identified", str(result.statistics['total_gaps']))
    summary_table.add_row("Avg Mapping Confidence", f"{result.statistics['average_mapping_confidence']:.2f}")
    
    console.print("\n", summary_table)
    
    # Rules by track
    track_table = Table(title="Rules by Track", box=box.ROUNDED)
    track_table.add_column("Track", style="cyan")
    track_table.add_column("Count", style="green")
    
    for track, count in result.statistics['rules_by_track'].items():
        track_table.add_row(track, str(count))
    
    console.print(track_table)
    
    # Gaps by type
    if result.statistics['total_gaps'] > 0:
        gap_table = Table(title="Gaps by Type", box=box.ROUNDED)
        gap_table.add_column("Type", style="cyan")
        gap_table.add_column("Count", style="yellow")
        
        for gap_type, count in result.statistics['gaps_by_type'].items():
            gap_table.add_row(gap_type, str(count))
        
        console.print(gap_table)


def _display_batch_summary(report):
    """Display batch processing summary."""
    
    summary_table = Table(title="Batch Processing Summary", box=box.ROUNDED)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Documents Processed", str(report['metadata']['num_documents_processed']))
    summary_table.add_row("Total Rules Extracted", str(report['summary']['total_rules_extracted']))
    summary_table.add_row("Total Gaps Identified", str(report['summary']['total_gaps_identified']))
    summary_table.add_row("Processing Time", f"{report['metadata']['total_processing_time_seconds']:.2f}s")
    
    console.print("\n", summary_table)
    
    # Coverage by track
    coverage_table = Table(title="Coverage by Track", box=box.ROUNDED)
    coverage_table.add_column("Track", style="cyan")
    coverage_table.add_column("Coverage %", style="green")
    coverage_table.add_column("Gaps", style="yellow")
    
    for track_id, coverage in report['coverage_analysis']['by_track'].items():
        coverage_table.add_row(
            coverage['track_name'],
            f"{coverage['coverage_percentage']:.1f}%",
            str(coverage['identified_gaps'])
        )
    
    console.print(coverage_table)


def _save_result_to_file(result, output_path: str):
    """Save extraction result to JSON file."""
    
    # Convert to dict
    result_dict = {
        'document_id': result.document_id,
        'extracted_rules': [
            {
                'rule_id': r.rule_id,
                'text_ar': r.text_ar,
                'track_id': r.track_id,
                'status': r.status.value,
                'mapping_confidence': r.mapping_confidence,
                'source': {
                    'document_name': r.source_reference.document_name,
                    'document_url': r.source_reference.document_url,
                    'page': r.source_reference.page_number,
                    'section': r.source_reference.section
                }
            }
            for r in result.extracted_rules
        ],
        'gaps': [
            {
                'gap_id': g.gap_id,
                'track_id': g.track_id,
                'gap_type': g.gap_type,
                'severity': g.severity,
                'extracted_rule': g.extracted_rule.text_ar,
                'recommendation': g.recommendation
            }
            for g in result.gaps
        ],
        'statistics': result.statistics,
        'processing_time_seconds': result.processing_time_seconds
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    cli()
