from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def tavily_search(query:str):
    try:
        response = client.search(
            query = query,
            max_results =5,
            search_depth="advanced"     
        )

        result = []

        for i,r in enumerate(response["results"],1):
            title = r.get("title","Unknown")
            url = r.get("url","no url")
            snippet = r.get("content","").strip()

            if len(snippet) > 300:
                snippet = snippet[:300].rsplit(" ",1)[0] + "..."
            

            result.append(f"{i}. **{title}**\n {url}\n {snippet}")

        return "\n\n".join(result)
    
    except Exception as e:
        return f"Error during Tavily search: {str(e)}"


