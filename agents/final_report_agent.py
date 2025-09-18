import os
import sqlite3
from typing import Dict, Any, List
from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv(override=True)






def fetch_summaries_from_db(query: str, topic_focus: str) -> List[Dict]:
    """Fetch relevant summaries from database."""
    try:
        conn = sqlite3.connect("youtube_research.db")
        cursor = conn.cursor()
        
        # Fetch summaries related to current query/topic
        cursor.execute("""
            SELECT video_url, video_title, summary, topic_focus, created_at
            FROM summaries 
            WHERE query = ? OR topic_focus LIKE ?
            ORDER BY created_at DESC
        """, (query, f"%{topic_focus}%"))
        
        results = cursor.fetchall()
        conn.close()
        
        summaries = []
        for row in results:
            summaries.append({
                'video_url': row[0],
                'video_title': row[1], 
                'summary': row[2],
                'topic_focus': row[3],
                'created_at': row[4]
            })
        
        return summaries
        
    except Exception as e:
        print(f"Error fetching summaries: {str(e)}")
        return []

def final_report_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node function that creates comprehensive final report from stored summaries."""
    
    llm = AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_API_BASE"),
        api_key=os.getenv("AZURE_API_KEY"),
        api_version=os.getenv("AZURE_API_VERSION"),
        azure_deployment=os.getenv("LLM_DEPLOYMENT_NAME")
    )
    
    query = state.get('query', '')
    topic_focus = state.get('topic_focus', '')
    
    # Fetch summaries from database
    stored_summaries = fetch_summaries_from_db(query, topic_focus)
    
    if not stored_summaries:
        return {
            "final_report": "No summaries found in database to create report.",
            "current_step": "report_failed",
            "errors": state.get('errors', []) + ["No stored summaries available"]
        }
    
    # Create comprehensive report prompt
    report_prompt = ChatPromptTemplate.from_template("""
    You are an expert research analyst. Create a comprehensive, detailed guide based on multiple YouTube video summaries.
    
    Original Query: {query}
    Topic Focus: {topic_focus}
    Number of Sources: {num_sources}
    
    Instructions:
    1. Synthesize ALL the information from the summaries below
    2. Create a complete, detailed guide about the topic
    3. Organize information logically with clear sections
    4. Include key insights, patterns, and conclusions
    5. Reference specific videos when mentioning important points
    6. Make it actionable and comprehensive
    7. Avoid repetition but ensure completeness
    
    Video Summaries:
    {summaries_text}
    
    Create a comprehensive research report in this format:
    
    # Complete Guide: {topic_focus}
    
    ## Executive Summary
    [High-level overview and key findings]
    
    ## Main Findings
    [Core insights organized by themes]
    
    ## Detailed Analysis
    [In-depth analysis with specific examples]
    
    ## Key Recommendations
    [Actionable recommendations based on the research]
    
    ## Sources Summary
    [Brief overview of video sources used]
    
    ## Conclusion
    [Final thoughts and next steps]
    """)
    
    try:
        # Prepare summaries text
        summaries_text = ""
        for i, summary in enumerate(stored_summaries, 1):
            summaries_text += f"\n--- Video {i}: {summary['video_title']} ---\n"
            summaries_text += f"URL: {summary['video_url']}\n"
            summaries_text += f"Summary: {summary['summary']}\n"
        
        # Format the prompt
        formatted_prompt = report_prompt.format(
            query=query,
            topic_focus=topic_focus,
            num_sources=len(stored_summaries),
            summaries_text=summaries_text #[:20000]  # Limit for token constraints
        )
        
        print(f"Generating final report from {len(stored_summaries)} summaries...")
        
        # Generate comprehensive report
        response = llm.invoke(formatted_prompt)
        final_report = response.content

        # Save report to DB
        conn = sqlite3.connect("youtube_research.db")
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO final_report (report_name, report)
                VALUES (?, ?)
            """, (topic_focus, final_report))
            conn.commit()
            print("✓ Final report saved to database")
        except Exception as e:
            print(f"Error saving final report: {e}")
        finally:
            conn.close()
        
        print("✓ Comprehensive final report generated")
        
        return {
            "final_report": final_report,
            "current_step": "report_completed",
            "sources_used": len(stored_summaries)
        }
        
    except Exception as e:
        print(f"Error in final_report_node: {str(e)}")
        return {
            "final_report": f"Error generating report: {str(e)}",
            "current_step": "report_failed",
            "errors": state.get('errors', []) + [str(e)]
        }