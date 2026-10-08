import os
import json
import urllib.request
import urllib.parse
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from bs4 import BeautifulSoup

app = FastAPI(title="Marketplace Search MCP", version="1.0.0")

class SearchRequest(BaseModel):
    query: str
    marketplace: str = "tokopedia"

def get_browserless_token():
    return os.environ.get("BROWSERLESS_TOKEN", "68c2e903363f3e677af7e37b2d310cd2")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "marketplace-mcp"}

@app.post("/search")
def search_marketplace(req: SearchRequest):
    token = get_browserless_token()
    query = req.query
    
    if req.marketplace.lower() == "tokopedia":
        query_params = f"token={token}&stealth&--disable-blink-features=AutomationControlled&--disable-http2"
        url = f"https://www.tokopedia.com/search?st=product&q={urllib.parse.quote(query)}"
        
        req_data = json.dumps({
            "url": url,
            "gotoOptions": {"waitUntil": "networkidle0", "timeout": 60000}
        }).encode()
        
        http_req = urllib.request.Request(
            f"http://192.168.100.19:3000/content?{query_params}",
            data=req_data,
            headers={"Content-Type": "application/json"}
        )
        
        try:
            with urllib.request.urlopen(http_req, timeout=90) as r:
                html = r.read().decode("utf-8", errors="ignore")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Browserless error: {str(e)}")
            
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        anchors = soup.find_all('a', class_=lambda c: c and 'Ui5-' in c)
        for a in anchors:
            href = a.get('href', '')
            price_el = None
            for s in a.find_all(string=True):
                if 'Rp' in s:
                    price_el = s
                    break
            texts = [t.strip() for t in a.find_all(string=True) if t.strip() and 'Rp' not in t]
            title = max(texts, key=len) if texts else ""
            price = price_el.strip() if price_el else "N/A"
            if title and 'Rp' in price:
                results.append({"title": title, "price": price, "link": href})
                
        return {"query": query, "marketplace": "tokopedia", "count": len(results), "items": results[:15]}
    else:
        raise HTTPException(status_code=400, detail="Only 'tokopedia' supported currently without residential proxy.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8095)
