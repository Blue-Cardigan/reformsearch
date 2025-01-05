# https://python.langchain.com/v0.2/docs/integrations/tools/bing_search/
# https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/create-bing-search-service-resource

import re
import os
import json
import requests
from typing import List
from langchain_core.documents import Document
from langchain_community.utilities import BingSearchAPIWrapper

from tools.logger import logger

### Env
# os.environ["BING_SUBSCRIPTION_KEY"] =  
# https://api.bing.microsoft.com/v7.0/images/search


### default search
def search(query, top_n=10, **kwargs) -> List[Document]:
    """Search Bing for the given query and return the top N results."""

    # load client
    bing_search = BingSearchAPIWrapper(k=top_n, **kwargs)

    # make search request
    bing_search_results = bing_search.results(query, num_results=top_n)
    # >> List[{title: str, link: str, snippet: str}]

    # format results
    bing_search_result_documents = []
    for result in bing_search_results:

        # if '{'Result': 'No good Bing Search Result was found'}'
        if 'Result' in result:
            resval = result['Result']
            if resval == 'No good Bing Search Result was found':
                logger.warning(f'Query "{query}" -> {resval}')
                return []
        
        # image search has no snippet...
        try:
            result['snippet'] = convert_html_to_markdown_content(result['snippet'])
            result['snippet'] = re.sub(r'[^a-zA-Z0-9\s]', '', result['snippet'])
        
        except Exception as e:
            pass
        
        doc = Document(result['snippet'], metadata=result)

        bing_search_result_documents.append(doc)
    
    if len(bing_search_result_documents) > top_n:
        bing_search_result_documents = bing_search_result_documents[:top_n]
    return bing_search_result_documents


def search_bing(query, top_n=10, **kwargs) -> List[Document]:
    """Search Bing for the given query and return the top N results."""

    os.environ["BING_SEARCH_URL"] = "https://api.bing.microsoft.com/v7.0/search"

    return search(query, top_n=top_n, **kwargs)