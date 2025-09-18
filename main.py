from graph.workflow import create_workflow
from graph.state import YouTubeResearchState

def run_youtube_research():
    """
    Main function to run the YouTube research workflow.
    """
    app = create_workflow()
    
    initial_state = {
        "query": "AI agents tutorial",
        "channels": ["@LangChain"],
        "max_results_per_query": 1,
        "language": "en",
       # "topic_focus": "AI agents",
        "video_urls": [],
        "video_metadata": [],
        "transcripts": {},
        "summaries": {},
        "storage_results": {},
        "final_report": "",
        "current_step": "starting",
        "errors": []
    }
    
    print("Starting YouTube Research Workflow...")
    
    try:
        final_state = app.invoke(initial_state)
        print("Workflow completed!")
        print(f"Video URLs found: {final_state.get('video_urls', [])}")
        print(f"Current step: {final_state.get('current_step', 'unknown')}")
        return final_state
    except Exception as e:
        print(f"Workflow failed: {str(e)}")
        return None

if __name__ == "__main__":
    result = run_youtube_research()


    