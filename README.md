# YouTube Research LangGraph
This project is a **multi-agent YouTube research workflow** using LangGraph and LangChain. It searches YouTube videos, extracts transcripts, summarizes content, stores results, and generates a final report.

## **Features**

- Search YouTube by **query**, **topics**, and **channels**
- Extract transcripts from videos
- Summarize transcripts automatically
- Store results in structured format
- Generate a final report
- Fully compatible with **LangChain agents**
- Async & sync YouTube search support

## **Workflow**

```

\[search] --> \[extract\_transcript] --> \[summarize] --> \[store] --> \[final\_report] --> \[END]

````

- **search** → search YouTube videos  
- **extract_transcript** → extract transcripts from videos  
- **summarize** → summarize transcripts  
- **store** → store results in structured format  
- **final_report** → generate final report  


## **State Structure**

`YouTubeResearchState` keeps track of the workflow data:

- **Input:** `query`, `channels`, `max_results_per_query`, `language`, `topic_focus`  
- **Data:** `video_urls`, `video_metadata`, `transcripts`, `summaries`, `storage_results`, `final_report`  
- **Status:** `current_step`, `errors`


## **Setup**

1. Install dependencies:

```bash
pip install -r requirements.txt
````

2. Create `.env` file with placeholders for API keys:

```env
YOUTUBE_API_KEY=your_youtube_api_key_here
```

> **Important:** Never commit real API keys to GitHub.


## **Usage**

Run the workflow:

```bash
python main.py
```

* Initializes the workflow
* Executes all agents in order
* Prints `video_urls` found and workflow status


## **YouTube Search Tool**

* Async version for high-performance searches:

```python
from tools.youtube_search_tool import youtube_search_function_async
```

* Sync wrapper for LangChain agents:

```python
from tools.youtube_search_tool import youtube_search_function_sync
```

* LangChain tools:

```python
from tools.youtube_search_tool import create_youtube_tool_async, create_youtube_tool_sync
```

## **Notes**

* Async calls use `aiohttp` and `asyncio`
* Errors are tracked in `errors` list of state
* The workflow can be extended with more agents or custom nodes

---

## **License**

MIT License

