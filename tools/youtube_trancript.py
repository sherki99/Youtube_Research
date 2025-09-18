import os
from typing import Dict, Any, List, Union
from langchain_openai import AzureChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain import hub
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
import json
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

class YouTubeTranscriptInput(BaseModel):
    """Input schema for YouTube Transcript Tool."""
    video_urls: Union[List[str], str] = Field(..., description="List of video urls to transcipt, it can also a single url")
    language: str = Field(default="en", description="Preferred transcript language")

def youtube_transcript_function(video_urls: Union[List[str], str], language: str = "en") -> str:
    """Extract transcripts from YouTube video URLs."""
    try:
        # Handle string input 
        if isinstance(video_urls, str):
            try:
                parsed = json.loads(video_urls)
                if isinstance(parsed, dict):
                    if "video_urls" in parsed:
                        video_urls = parsed["video_urls"]
                    elif "videos" in parsed:
                        video_urls = [v.get("url") for v in parsed["videos"] if v.get("url")]
                    else:
                        video_urls = list(parsed.values()) if parsed else []
                elif isinstance(parsed, list):
                    video_urls = parsed
                else:
                    video_urls = [video_urls] if video_urls.startswith("http") else []
            except:
                video_urls = [video_urls] if video_urls.startswith("http") else []
        
        if not video_urls:
            return json.dumps({
                'error': 'No valid video URLs provided',
                'total_videos_processed': 0,
                'successful_transcripts': 0,
                'transcripts': {},
                'processing_date': datetime.now().isoformat()
            })
        
        results = {}
        errors = []
        
        for url in video_urls:
            try:
                video_id = extract_video_id(url)
                if not video_id:
                    errors.append(f"Invalid URL format: {url}")
                    continue
                    
                transcript_data = get_video_transcript(video_id, language)
                if transcript_data:
                    results[video_id] = {
                        'video_id': video_id,
                        'url': url,
                        'transcript': transcript_data['text'],
                        'language': transcript_data['language'],
                        'word_count': len(transcript_data['text'].split()),
                        'is_generated': transcript_data.get('is_generated', False)
                    }
                else:
                    errors.append(f"No transcript available for: {url}")
                    
            except Exception as e:
                errors.append(f"Error processing {url}: {str(e)}")
        
        return json.dumps({
            'total_videos_processed': len(video_urls),
            'successful_transcripts': len(results),
            'failed_extractions': len(errors),
            'transcripts': results,
            'errors': errors,
            'processing_date': datetime.now().isoformat()
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            'error': f"Transcript extraction failed: {str(e)}",
            'total_videos_processed': 0,
            'successful_transcripts': 0,
            'transcripts': {},
            'processing_date': datetime.now().isoformat()
        })

def extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL."""
    if not url or not isinstance(url, str):
        return None
        
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([^&]+)',
        r'(?:https?://)?(?:www\.)?youtu\.be/([^?]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([^?]+)',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_video_transcript(video_id: str, preferred_language: str = "en") -> Dict[str, Any]:
    """Get transcript for a single video."""
    try:

        # proxy_config = WebshareProxyConfig(
        #     proxy_host="195.85.23.92",
        #     proxy_port=80
        # )
        ytt_api = YouTubeTranscriptApi()

        transcript_list = ytt_api.list(video_id)
        transcript = None
        
        # Try preferred language (manual first)
        try:
            transcript = transcript_list.find_manually_created_transcript([preferred_language])
        except:
            try:
                transcript = transcript_list.find_generated_transcript([preferred_language])
            except:
                pass
        
        # Try English if not found
        if not transcript and preferred_language != 'en':
            try:
                transcript = transcript_list.find_manually_created_transcript(['en'])
            except:
                try:
                    transcript = transcript_list.find_generated_transcript(['en'])
                except:
                    pass
        
        # Get any available transcript
        if not transcript:
            try:
                for t in transcript_list:
                    transcript = t
                    break
            except:
                pass
        
        if transcript:
            transcript_data = transcript.fetch()
            full_text = ' '.join([entry.text for entry in transcript_data if entry.text])
            cleaned_text = clean_transcript_text(full_text)
            
            return {
                'text': cleaned_text,
                'language': transcript.language_code,
                'is_generated': getattr(transcript, 'is_generated', False)
            }
                
        return None
        
    except Exception as e:
        print(f"Error getting transcript for {video_id}: {str(e)}")
        return None

def clean_transcript_text(text: str) -> str:
    """Clean transcript text."""
    if not text:
        return ""
    # Add cleaning logic here
    return text.strip()

def create_youtube_transcript_tool():
    """Create YouTube transcript tool for LangChain agents."""
    return StructuredTool.from_function(
        name="youtube_transcript",
        description="Extract transcripts from YouTube video URLs",
        func=youtube_transcript_function,
        args_schema=YouTubeTranscriptInput
    )

