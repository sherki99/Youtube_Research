import os
from typing import Dict, Any, List
from langchain_openai import AzureChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain import hub
from tools.youtube_search_tool import create_youtube_tool_sync
from dotenv import load_dotenv
import re
import json

load_dotenv(override=True)

def search_video_node(state: Dict[str, Any]) -> Dict[str, Any]: 
    """
    Node function that searches for YouTube videos.
    """
    llm = AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_API_BASE"),
        api_key=os.getenv("AZURE_API_KEY"),
        api_version=os.getenv("AZURE_API_VERSION"),
        azure_deployment=os.getenv("LLM_DEPLOYMENT_NAME")     
    )

    tools = [create_youtube_tool_sync()]

    # Create agent with system prompt
    prompt = hub.pull("hwchase17/openai-functions-agent")
    agent = create_openai_functions_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, return_intermediate_steps=True)

    # Updated search input to be more specific
    search_input = {
        "input": f"""
        Use the youtube_search tool to find videos with these parameters:
        - topics: {[state.get('query', '')]} 
        - channels: {state.get('channels', [])}
        - max_results_per_query: {state.get('max_results_per_query', 5)}
        
        Return the video URLs from the search results.
        """
    }

    try: 
        result = agent_executor.invoke(search_input)
        
        # FIXED: Extract URLs from intermediate steps (tool outputs)
        video_urls = []
        video_metadata = []
        
        # Check intermediate steps for tool outputs
        if 'intermediate_steps' in result:
            for step in result['intermediate_steps']:
                if len(step) >= 2:
                    tool_output = step[1]  # Second element is tool output
                    if isinstance(tool_output, str):
                        try:
                            # Parse JSON from tool output
                            json_data = json.loads(tool_output)
                            if 'video_urls' in json_data:
                                video_urls.extend(json_data['video_urls'])
                            if 'videos' in json_data:
                                video_metadata.extend(json_data['videos'])
                        except json.JSONDecodeError:
                            # Fallback to regex
                            youtube_urls = re.findall(r'https://www\.youtube\.com/watch\?v=[\w-]+', tool_output)
                            video_urls.extend(youtube_urls)
        
        # Fallback: parse from final output if no intermediate steps
        if not video_urls:
            output = result.get("output", "")
            youtube_urls = re.findall(r'https://www\.youtube\.com/watch\?v=[\w-]+', output)
            video_urls.extend(youtube_urls)
            
        # Remove duplicates
        video_urls = list(set(video_urls))
        
        print(f"Extracted {len(video_urls)} video URLs")
        
        return {
            "video_urls": video_urls,
            "video_metadata": video_metadata,
            "current_step": "search_completed"
        }

    except Exception as e:
        print(f"Error in search_video_node: {str(e)}")
        return {
            "video_urls": [],
            "video_metadata": [],
            "current_step": "search_failed",
            "errors": state.get('errors', []) + [str(e)]
        }

