"""
Async YouTube Search Tool - Clean version
Search videos by topics, channels, or topics within channels using YouTube Data API.
"""

import os
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool
import aiohttp
import asyncio
from dotenv import load_dotenv

load_dotenv(override=True)

class YouTubeSearchInput(BaseModel):
    query: str = Field(description="Main search query/topic")
    topics: Optional[List[str]] = Field(None, description="Additional specific topics")
    channels: Optional[List[str]] = Field(None, description="Channel names to search in")
    max_results_per_query: int = Field(default=5, description="Max videos per query")


async def youtube_search_function_async(
    query: str,
    topics: Optional[List[str]] = None,
    channels: Optional[List[str]] = None,
    max_results_per_query: int = 2,
) -> str:
    """
    Search YouTube for videos by topics, channels, or topics within channels.

    Parameters:
        query (str): Main search query/topic.
        topics (list[str], optional): Additional topics to search for.
        channels (list[str], optional): Channels to search in.
        max_results_per_query (int): Maximum videos to retrieve per query (default 2).

    Returns:
        str: JSON string containing video metadata, URLs, and search summary.
    """
    try:
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            return json.dumps({"error": "YOUTUBE_API_KEY not set", "videos": []})

        all_videos = []
        base_url = "https://www.googleapis.com/youtube/v3"

        async def fetch_json(session, url, params):
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()

        async def search_videos(query_str: str, max_results: int) -> List[Dict[str, Any]]:
            async with aiohttp.ClientSession() as session:
                data = await fetch_json(session, f"{base_url}/search", {
                    'part': 'id,snippet', 'q': query_str, 'type': 'video',
                    'maxResults': max_results, 'order': 'relevance', 'key': api_key
                })
            return [
                {
                    "video_id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    "channel_name": item["snippet"]["channelTitle"],
                    "published_at": item["snippet"]["publishedAt"],
                }
                for item in data.get('items', [])
            ]

        async def get_channel_id(channel_name: str) -> Optional[str]:
            async with aiohttp.ClientSession() as session:
                data = await fetch_json(session, f"{base_url}/search", {
                    'part': 'id', 'q': channel_name, 'type': 'channel', 'maxResults': 1, 'key': api_key
                })
            return data['items'][0]['id']['channelId'] if data.get('items') else None

        async def get_channel_videos(channel_name: str, max_results: int) -> List[Dict[str, Any]]:
            channel_id = await get_channel_id(channel_name)
            if not channel_id:
                return []

            async with aiohttp.ClientSession() as session:
                channel_data = await fetch_json(session, f"{base_url}/channels", {
                    'part': 'contentDetails', 'id': channel_id, 'key': api_key
                })
                uploads_playlist = channel_data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
                playlist_data = await fetch_json(session, f"{base_url}/playlistItems", {
                    'part': 'snippet', 'playlistId': uploads_playlist, 'maxResults': max_results, 'key': api_key
                })

            return [
                {
                    "video_id": item["snippet"]["resourceId"]["videoId"],
                    "title": item["snippet"]["title"],
                    "url": f"https://www.youtube.com/watch?v={item['snippet']['resourceId']['videoId']}",
                    "channel_name": item["snippet"]["channelTitle"],
                    "published_at": item["snippet"]["publishedAt"],
                }
                for item in playlist_data.get('items', [])
            ]

        async def search_in_channel(topic: str, channel_id: str, max_results: int) -> List[Dict[str, Any]]:
            async with aiohttp.ClientSession() as session:
                data = await fetch_json(session, f"{base_url}/search", {
                    'part': 'id,snippet', 'q': topic, 'type': 'video',
                    'channelId': channel_id, 'maxResults': max_results,
                    'order': 'relevance', 'key': api_key
                })
            return [
                {
                    "video_id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    "channel_name": item["snippet"]["channelTitle"],
                    "published_at": item["snippet"]["publishedAt"],
                }
                for item in data.get('items', [])
            ]

        # ----- MAIN SEARCH LOGIC -----
        # Always search the main query first
        main_videos = await search_videos(query, max_results_per_query)
        for v in main_videos:
            v["source_type"] = "main_query"
            v["source_query"] = query
        all_videos.extend(main_videos)

        # Then apply additional filters based on what's provided
        if topics and not channels:
            # Search additional topics combined with main query
            for topic in topics:
                videos = await search_videos(f"{query} {topic}", max_results_per_query)
                for v in videos:
                    v["source_type"] = "topic"
                    v["source_query"] = f"{query} {topic}"
                all_videos.extend(videos)

        elif channels and not topics:
            # Search main query in specific channels
            for channel in channels:
                channel_id = await get_channel_id(channel)
                if channel_id:
                    videos = await search_in_channel(query, channel_id, max_results_per_query)
                    for v in videos:
                        v["source_type"] = "channel"
                        v["source_query"] = f"{query} in {channel}"
                    all_videos.extend(videos)

        elif topics and channels:
            # Search topics combined with main query within specific channels
            for channel in channels:
                channel_id = await get_channel_id(channel)
                if not channel_id:
                    continue
                for topic in topics:
                    search_term = f"{query} {topic}"
                    videos = await search_in_channel(search_term, channel_id, max_results_per_query)
                    for v in videos:
                        v["source_type"] = "topic+channel"
                        v["source_query"] = f"{search_term} in {channel}"
                    all_videos.extend(videos)

        return json.dumps({
            "main_query": query,
            "topics_searched": topics or [],
            "channels_searched": channels or [],
            "total_results": len(all_videos),
            "video_urls": [v["url"] for v in all_videos],
            "videos": all_videos,
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "video_urls": [], "videos": []})

# sync wrapper for the async function
def youtube_search_function_sync(
    query: str,
    topics: Optional[List[str]] = None,
    channels: Optional[List[str]] = None,
    max_results_per_query: int = 2,
) -> str:
    """
    Synchronous wrapper for YouTube search that can be used with LangChain agents.
    """
    try:
        # Run the async function in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                youtube_search_function_async(query, topics, channels, max_results_per_query)
            )
            return result
        finally:
            loop.close()
    except Exception as e:
        return json.dumps({"error": str(e), "video_urls": [], "videos": []})


# ----- LANGCHAIN TOOL CREATION -----
def create_youtube_tool_async():
    return StructuredTool.from_function(
        name="youtube_search_async",
        description="Search YouTube for videos by main query with optional topics and channels filters",
        func=youtube_search_function_async,
        args_schema=YouTubeSearchInput,
    )

def create_youtube_tool_sync():
    """Create a synchronous YouTube search tool for LangChain agents."""
    return StructuredTool.from_function(
        name="youtube_search",
        description="Search YouTube for videos by main query with optional topics and channels filters",
        func=youtube_search_function_sync,
        args_schema=YouTubeSearchInput
    )