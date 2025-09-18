import os
from typing import Dict, Any
from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import json

load_dotenv(override=True)

def create_summary_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node function that creates clean summaries from transcripts."""
    
    llm = AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_API_BASE"),
        api_key=os.getenv("AZURE_API_KEY"),
        api_version=os.getenv("AZURE_API_VERSION"),
        azure_deployment=os.getenv("LLM_DEPLOYMENT_NAME")
    )
    
    # Create a prompt template for summarization
    summary_prompt = ChatPromptTemplate.from_template("""
    You are an expert content summarizer. Your task is to create clean, well-structured summaries of YouTube video transcripts.
    
    Topic Focus: {topic_focus}
    
    Instructions:
    1. Clean up the transcript by removing filler words, repetitions, and unclear segments
    2. Organize the content into clear, logical sections
    3. Preserve all important information and key insights
    4. Focus on content relevant to: {topic_focus}
    5. Create a readable, professional summary
    6. Include key quotes when they add value
    7. Maintain the original meaning and context
    
 
    Video URL: {video_url}
    
    Raw Transcript:
    {transcript_text}
    
    Please provide a well-structured summary in the following format:
    
    ## Video Summary
    
    ### Key Points:
    - [Main points in bullet format]
    
    ### Detailed Summary:
    [Organized narrative summary with clear paragraphs]
    
    ### Important Quotes:
    [Any significant quotes that add value]
    
    ### Relevance to Topic:
    [How this content relates to the topic focus]
    """)
    
    transcripts = state.get('transcripts', {})
    summaries = {}
    topic_focus = state.get('topic_focus', 'general content')
    
    if not transcripts:
        print("No transcripts found to summarize")
        return {
            "summaries": {},
            "current_step": "summary_failed",
            "errors": state.get('errors', []) + ["No transcripts available for summarization"]
        }
    
    try:
        print(f"Creating summaries for {len(transcripts)} transcripts...")
        
        for video_url, transcript_data in transcripts.items():
            try:
                # Extract transcript text
                if isinstance(transcript_data, dict):
                    transcript_text = transcript_data.get('transcript', '')
                   # video_title = transcript_data.get('title', 'Unknown Title')
                else:
                    transcript_text = str(transcript_data)
                    #video_title = 'Unknown Title'
                
                if not transcript_text or len(transcript_text.strip()) < 50:
                    print(f"Skipping video {video_url} - insufficient transcript content")
                    continue
                
                # Format the prompt
                formatted_prompt = summary_prompt.format(
                    topic_focus=topic_focus,
                  #  video_title=video_title,
                    video_url=video_url,
                    transcript_text=transcript_text[:15000]  # Limit length to avoid token limits
                )
                
                # Generate summary
                print(f"Generating summary for: {video_url}")
                response = llm.invoke(formatted_prompt)
                
                summaries[video_url] = {
              #      'video_title': video_title,
                    'video_url': video_url,
                    'summary': response.content,
                    'original_transcript_length': len(transcript_text),
                    'summary_length': len(response.content),
                    'topic_focus': topic_focus
                }
                
                print(f"✓ Summary created for: {video_url}")
                
            except Exception as e:
                print(f"Error summarizing video {video_url}: {str(e)}")
                summaries[video_url] = {
               #     'video_title': video_title,
                    'video_url': video_url,
                    'summary': f"Error creating summary: {str(e)}",
                    'error': True
                }
                continue
        
        print(f"Successfully created {len([s for s in summaries.values() if not s.get('error')])} summaries")
        
        return {
            "summaries": summaries,
            "current_step": "summary_completed"
        }
        
    except Exception as e:
        print(f"Error in create_summary_node: {str(e)}")
        return {
            "summaries": {},
            "current_step": "summary_failed", 
            "errors": state.get('errors', []) + [str(e)]
        }