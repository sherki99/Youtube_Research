import sqlite3
import os
import json
from typing import Dict, Any
from datetime import datetime

def create_database():
    """Create SQLite database and tables if they don't exist."""
    db_path = "youtube_research.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create summaries table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_url TEXT UNIQUE NOT NULL,
            video_title TEXT NOT NULL,
            summary TEXT NOT NULL,
            topic_focus TEXT NOT NULL,
            query TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            original_length INTEGER,
            summary_length INTEGER
        )
    """)



    # final_report table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS final_report (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_name TEXT UNIQUE NOT NULL,
            report TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def storage_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node function that stores summaries in SQLite database."""
    
    try:
        # Create database if it doesn't exist
        create_database()
        
        summaries = state.get('summaries', {})
        query = state.get('query', 'unknown_query')
        topic_focus = state.get('topic_focus', 'general')
        
        if not summaries:
            return {
                "storage_results": {"status": "failed", "message": "No summaries to store"},
                "current_step": "storage_failed",
                "errors": state.get('errors', []) + ["No summaries available for storage"]
            }
        
        conn = sqlite3.connect("youtube_research.db")
        cursor = conn.cursor()
        
        stored_count = 0
        errors = []
        
        for video_url, summary_data in summaries.items():
            try:
                # Skip if summary has error
                if summary_data.get('error'):
                    continue
                
                # Insert or replace summary
                cursor.execute("""
                    INSERT OR REPLACE INTO summaries 
                    (video_url, video_title, summary, topic_focus, query, original_length, summary_length)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    video_url,
                    summary_data.get('video_title', 'Unknown Title'),
                    summary_data.get('summary', ''),
                    topic_focus,
                    query,
                    summary_data.get('original_transcript_length', 0),
                    summary_data.get('summary_length', 0)
                ))
                
                stored_count += 1
                
            except Exception as e:
                errors.append(f"Error storing {video_url}: {str(e)}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"✓ Stored {stored_count} summaries in database")
        
        return {
            "storage_results": {
                "status": "success",
                "stored_count": stored_count,
                "errors": errors
            },
            "current_step": "storage_completed"
        }
        
    except Exception as e:
        print(f"Error in storage_node: {str(e)}")
        return {
            "storage_results": {"status": "failed", "message": str(e)},
            "current_step": "storage_failed",
            "errors": state.get('errors', []) + [str(e)]
        }
