from typing import TypedDict, List, Dict, Optional, Any

class YouTubeResearchState(TypedDict):  
    
    # Input parameters
    query: str
    channels: List[str]
    max_results_per_query: int
    language: str
    topic_focus: str
    
    # Data flow between agents
    video_urls: List[str]
    video_metadata: List[Dict[str, Any]]
    transcripts: Dict[str, Dict[str, Any]]
    summaries: Dict[str, Dict[str, Any]]
    storage_results: Dict[str, Any]
    final_report: str
    
    # Processing status
    current_step: str
    errors: List[str]
