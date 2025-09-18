import os
from typing import Dict, Any, List
from langchain_openai import AzureChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain import hub
from tools.youtube_trancript import create_youtube_transcript_tool
from dotenv import load_dotenv
import re
import json


load_dotenv(override=True)



def extract_transcripts_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node function that extracts transcripts from video URLs."""
    llm = AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_API_BASE"),
        api_key=os.getenv("AZURE_API_KEY"),
        api_version=os.getenv("AZURE_API_VERSION"),
        azure_deployment=os.getenv("LLM_DEPLOYMENT_NAME")     
    )

    tools = [create_youtube_transcript_tool()]
    prompt = hub.pull("hwchase17/openai-functions-agent")
    agent = create_openai_functions_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, return_intermediate_steps=True)

    transcript_input = {
        "input": f"""
        Use the youtube_transcript tool to extract transcripts from these video URLs:
        Video URLs: {state.get('video_urls', [])}
        Language preference: {state.get('language', 'en')}
        
        Extract clean, complete transcripts from all videos.
        """
    }

    try:
        result = agent_executor.invoke(transcript_input)
        
        # Extract transcripts from intermediate steps
        transcripts = {}
        
        if 'intermediate_steps' in result:
            for step in result['intermediate_steps']:
                if len(step) >= 2:
                    tool_output = step[1]
                    if isinstance(tool_output, str):
                        try:
                            json_data = json.loads(tool_output)
                            if 'transcripts' in json_data:
                                transcripts.update(json_data['transcripts'])
                        except json.JSONDecodeError:
                            continue
        
        print(f"Extracted {len(transcripts)} transcripts")
        
        return {
            "transcripts": transcripts,
            "current_step": "transcript_completed"
        }

    except Exception as e:
        print(f"Error in extract_transcripts_node: {str(e)}")
        return {
            "transcripts": {},
            "current_step": "transcript_failed",
            "errors": state.get('errors', []) + [str(e)]
        }