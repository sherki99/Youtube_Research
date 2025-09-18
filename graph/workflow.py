# Updated graph/workflow.py
from langgraph.graph import StateGraph, END
from typing import Dict, Any
from graph.state import YouTubeResearchState
from agents.search_agent import search_video_node
from agents.extract_transcript_agent import extract_transcripts_node
from agents.summary_agent import create_summary_node
from agents.store_agents import storage_node
from agents.final_report_agent import final_report_node

def create_workflow():
    """Create the workflow for YouTube multi-agent system."""
    
    workflow = StateGraph(YouTubeResearchState)
    
    # Add nodes/agents
    workflow.add_node("search", search_video_node)
    workflow.add_node("extract_transcript", extract_transcripts_node)
    workflow.add_node("summarize", create_summary_node)
    workflow.add_node("store", storage_node)
    workflow.add_node("final_report", final_report_node)
    
    # Set entry point
    workflow.set_entry_point("search")
    
    # Add workflow edges
    workflow.add_edge("search", "extract_transcript")
    workflow.add_edge("extract_transcript", "summarize")
    workflow.add_edge("summarize", "store")
    workflow.add_edge("store", "final_report")
    workflow.add_edge("final_report", END)
    
    return workflow.compile()