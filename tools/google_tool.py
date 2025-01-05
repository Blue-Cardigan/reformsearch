import os
from dotenv import load_dotenv
from typing import List
import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from langchain_core.documents import Document

from tools.logger import logger

load_dotenv()

def search_google(query: str, top_n: int = 5) -> List[Document]:
    """Search Google for the given query and return the top N results."""
    
    # Force reload environment variables
    load_dotenv(override=True)
    
    # Validate environment variables
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    
    logger.debug(f"Using API Key: {api_key[:10]}...")
    logger.debug(f"Using CSE ID: {cse_id}")
    
    if not api_key or not cse_id:
        logger.error("Missing GOOGLE_API_KEY or GOOGLE_CSE_ID in environment variables")
        return []
        
    try:
        # Initialize the Google Custom Search API service
        service = build(
            "customsearch", "v1",
            developerKey=api_key,
            cache_discovery=False
        )

        # Create a custom search instance
        result = service.cse().list(
            q=query,
            cx=cse_id,
            num=min(top_n, 5)  # Google CSE has a max of 10 results per query
        ).execute()

        # Format results
        documents = []
        if 'items' in result:
            for item in result['items']:
                # Clean snippet text
                snippet = item.get('snippet', '')
                snippet = re.sub(r'[^a-zA-Z0-9\s]', '', snippet)

                # Create document
                doc = Document(
                    page_content=snippet,
                    metadata={
                        'title': item.get('title', ''),
                        'link': item.get('link', ''),
                        'search_time': result.get('searchTime', '')
                    }
                )
                documents.append(doc)

        logger.info(f"Successfully retrieved {len(documents)} results for query: {query}")
        return documents

    except HttpError as e:
        logger.error(f"Google API HTTP Error: {e.resp.status} - {e.content}")
        return []
    except Exception as e:
        logger.error(f"Google search error: {str(e)}")
        return [] 