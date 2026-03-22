import requests
import json
from typing import Dict, Any, Optional, Union
import re

class NetworkController:
    def http_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
        timeout: float = 10.0,
        follow_redirects: bool = True,
        extract: Optional[str] = None,
        response_format: str = "auto"
    ) -> Dict[str, Any]:
        
        try:
            resp = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=body if isinstance(body, (str, bytes)) else json.dumps(body),
                timeout=timeout,
                allow_redirects=follow_redirects
            )
            
            content_type = resp.headers.get("Content-Type", "")
            is_json = "application/json" in content_type or response_format == "json"
            
            result_data = None
            
            if is_json:
                try:
                    data = resp.json()
                    if extract:
                        # Simple JSON Path extraction: key.subkey[0]
                        keys = extract.replace("[", ".").replace("]", "").split(".")
                        curr = data
                        for k in keys:
                            if k == "": continue
                            if isinstance(curr, dict): curr = curr.get(k)
                            elif isinstance(curr, list) and k.isdigit(): curr = curr[int(k)]
                            else: curr = None; break
                        result_data = curr
                    else:
                        result_data = data
                except ValueError:
                    result_data = resp.text
            else:
                # Text / HTML
                text = resp.text
                if extract and "html" in content_type:
                    # Try BeautifulSoup for CSS selectors
                    try:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(text, 'html.parser')
                        selection = soup.select(extract)
                        result_data = [str(s) for s in selection]
                    except ImportError:
                        result_data = f"Error: BeautifulSoup4 not installed, cannot use CSS selector extract '{extract}'"
                    except Exception as e:
                         result_data = f"Extraction Error: {e}"
                else:
                    result_data = text

            return {
                "status_code": resp.status_code,
                "headers": dict(resp.headers),
                "data": result_data,
                "url": resp.url
            }

        except Exception as e:
            return {"error": str(e)}
