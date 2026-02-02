"""
MCP Server for Financial Documents Parsing.

This server exposes document parsing functionality through the Model Context Protocol (MCP).
It integrates with aiXplain for LLM processing and maintains the RAG pipeline.

The MCP server provides tools for:
- Parsing PDFs and web pages
- Extracting Saudi government financial rules
- Processing with aiXplain models
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.parser import DocumentParser
from src.agent import FinancialRulesAgent
from src.config import config
from loguru import logger


# Initialize MCP server
app = Server("financial-rules-parser")

# Initialize components
parser = DocumentParser()
agent = None  # Will be initialized when needed


def get_agent() -> FinancialRulesAgent:
    """Lazy initialization of agent to avoid startup delays."""
    global agent
    if agent is None:
        try:
            agent = FinancialRulesAgent(api_key=config.aixplain.api_key)
            logger.info("Financial Rules Agent initialized for MCP server")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise
    return agent


@app.list_tools()
async def list_tools() -> List[Tool]:
    """
    List available MCP tools for financial document processing.
    
    Returns:
        List of Tool objects describing available operations
    """
    return [
        Tool(
            name="parse_document",
            description=(
                "Parse a Saudi government financial document (PDF or web page) "
                "and extract its text content. Supports Arabic and English documents. "
                "This is the first step before rule extraction."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL of the document (PDF or web page)"
                    },
                    "name": {
                        "type": "string",
                        "description": "Human-readable name for the document"
                    }
                },
                "required": ["url", "name"]
            }
        ),
        Tool(
            name="extract_financial_rules",
            description=(
                "Extract financial rules from a Saudi government document using aiXplain AI models. "
                "Uses RAG (Retrieval-Augmented Generation) with ChromaDB vector database. "
                "Automatically maps rules to financial tracks: Contracts (العقود), "
                "Salaries (الرواتب), or Invoices (الفواتير). "
                "Performs gap analysis against existing rules."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL of the document to process"
                    },
                    "name": {
                        "type": "string",
                        "description": "Document name for identification"
                    },
                    "enable_rag": {
                        "type": "boolean",
                        "description": "Enable RAG mode (default: true)",
                        "default": True
                    }
                },
                "required": ["url", "name"]
            }
        ),
        Tool(
            name="get_predefined_tracks",
            description=(
                "Get the list of predefined Saudi financial tracks with their current rules. "
                "Returns: Contracts (العقود), Salaries (الرواتب), Invoices (الفواتير) "
                "with their validation rules and requirements."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="batch_process_documents",
            description=(
                "Process multiple Saudi government documents in batch. "
                "Each document is parsed, rules extracted using aiXplain, "
                "and mapped to financial tracks. Returns aggregated results."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "documents": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string"},
                                "name": {"type": "string"}
                            },
                            "required": ["url", "name"]
                        },
                        "description": "List of documents to process"
                    }
                },
                "required": ["documents"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """
    Execute MCP tool with given arguments.
    
    Args:
        name: Tool name to execute
        arguments: Tool-specific arguments
        
    Returns:
        List of TextContent with results
    """
    try:
        if name == "parse_document":
            result = await parse_document_tool(arguments)
        elif name == "extract_financial_rules":
            result = await extract_financial_rules_tool(arguments)
        elif name == "get_predefined_tracks":
            result = await get_predefined_tracks_tool()
        elif name == "batch_process_documents":
            result = await batch_process_documents_tool(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
    
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        error_result = {
            "status": "error",
            "error": str(e),
            "tool": name
        }
        return [TextContent(type="text", text=json.dumps(error_result, ensure_ascii=False, indent=2))]


async def parse_document_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse document from URL.
    
    Args:
        args: {"url": str, "name": str}
        
    Returns:
        Parsed document metadata and text preview
    """
    url = args.get("url")
    name = args.get("name")
    
    if not url or not name:
        raise ValueError("Both 'url' and 'name' are required")
    
    logger.info(f"Parsing document: {name} from {url}")
    
    # Parse document
    doc = parser.parse(url, name)
    
    # Return metadata and preview
    return {
        "status": "success",
        "document": {
            "id": doc.id,
            "name": doc.name,
            "source_url": doc.source_url,
            "content_length": len(doc.content),
            "content_preview": doc.content[:500] + "..." if len(doc.content) > 500 else doc.content,
            "language": doc.metadata.get("language", "unknown"),
            "parsed_at": doc.metadata.get("parsed_at", "")
        }
    }


async def extract_financial_rules_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract financial rules using aiXplain agent.
    
    Args:
        args: {"url": str, "name": str, "enable_rag": bool}
        
    Returns:
        Extracted rules, track mappings, and gap analysis
    """
    url = args.get("url")
    name = args.get("name")
    enable_rag = args.get("enable_rag", True)
    
    if not url or not name:
        raise ValueError("Both 'url' and 'name' are required")
    
    logger.info(f"Extracting rules from: {name} (RAG={enable_rag})")
    
    # Get agent instance
    financial_agent = get_agent()
    
    # Process document
    result = financial_agent.process_document(
        name=name,
        url=url,
        enable_rag=enable_rag
    )
    
    # Format response
    return {
        "status": "success",
        "document": {
            "name": name,
            "url": url
        },
        "extraction": {
            "total_rules": result.get("statistics", {}).get("total_rules", 0),
            "rules_by_track": result.get("statistics", {}).get("rules_by_track", {}),
            "extracted_rules": [
                {
                    "text_ar": rule.get("text_ar", ""),
                    "text_en": rule.get("text_en", ""),
                    "track": rule.get("track", ""),
                    "confidence": rule.get("confidence", 0.0),
                    "source": rule.get("source", "")
                }
                for rule in result.get("extracted_rules", [])
            ]
        },
        "gap_analysis": {
            "new_rules": result.get("statistics", {}).get("new_rules", 0),
            "existing_rules": result.get("statistics", {}).get("existing_rules", 0),
            "gaps": result.get("gap_analysis", [])
        },
        "processing_time": result.get("processing_time_seconds", 0),
        "rag_enabled": enable_rag
    }


async def get_predefined_tracks_tool() -> Dict[str, Any]:
    """
    Get predefined financial tracks.
    
    Returns:
        All tracks with their current rules
    """
    from src.tracks import get_all_tracks
    
    tracks = get_all_tracks()
    
    return {
        "status": "success",
        "tracks": [
            {
                "id": track.track_id,
                "name_ar": track.name_ar,
                "name_en": track.name_en,
                "description": track.description,
                "current_rules": [
                    {
                        "rule_id": rule.rule_id,
                        "description": rule.description,
                        "source": rule.source,
                        "priority": rule.priority
                    }
                    for rule in track.current_rules
                ]
            }
            for track in tracks
        ]
    }


async def batch_process_documents_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process multiple documents in batch.
    
    Args:
        args: {"documents": [{"url": str, "name": str}, ...]}
        
    Returns:
        Aggregated results from all documents
    """
    documents = args.get("documents", [])
    
    if not documents:
        raise ValueError("No documents provided")
    
    logger.info(f"Batch processing {len(documents)} documents")
    
    # Get agent instance
    financial_agent = get_agent()
    
    results = []
    for doc in documents:
        try:
            result = financial_agent.process_document(
                name=doc["name"],
                url=doc["url"],
                enable_rag=True
            )
            results.append({
                "document": doc,
                "status": "success",
                "rules_extracted": result.get("statistics", {}).get("total_rules", 0),
                "processing_time": result.get("processing_time_seconds", 0)
            })
        except Exception as e:
            logger.error(f"Failed to process {doc['name']}: {e}")
            results.append({
                "document": doc,
                "status": "error",
                "error": str(e)
            })
    
    # Aggregate statistics
    total_rules = sum(r.get("rules_extracted", 0) for r in results if r["status"] == "success")
    successful = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "error")
    
    return {
        "status": "success",
        "summary": {
            "total_documents": len(documents),
            "successful": successful,
            "failed": failed,
            "total_rules_extracted": total_rules
        },
        "results": results
    }


async def main():
    """Run the MCP server."""
    logger.info("Starting Financial Rules MCP Server")
    logger.info("Powered by aiXplain with ChromaDB vector storage")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
