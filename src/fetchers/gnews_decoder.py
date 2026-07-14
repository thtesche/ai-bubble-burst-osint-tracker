"""
Google News URL Decoder — async implementation.

Decodes Google News redirect URLs (e.g. news.google.com/rss/articles/...)
into the original source article URLs.

Adapted from https://github.com/SSujitX/google-news-url-decoder
MIT License
"""

import asyncio
import json
from typing import Optional

from urllib.parse import quote, urlparse

import httpx
from selectolax.parser import HTMLParser


class GoogleDecoderAsync:
    """Async Google News URL decoder using httpx."""

    def __init__(self, proxy: Optional[str] = None):
        """
        Initialize the GoogleDecoder class.

        Args:
            proxy: Proxy URL. Supported formats:
                   - HTTP/HTTPS: http://user:pass@host:port
                   - SOCKS5: socks5://user:pass@host:port
        """
        self.proxy = proxy
        self.client = httpx.AsyncClient(
            proxy=self.proxy, follow_redirects=True
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    def get_base64_str(self, source_url: str) -> dict:
        """
        Extracts the base64 string from a Google News URL.

        Args:
            source_url: The Google News article URL.

        Returns:
            dict with 'status' and 'base64_str' (if successful)
            or 'status' and 'message' (if failed).
        """
        try:
            url = urlparse(source_url)
            path = url.path.split("/")
            if (
                url.hostname == "news.google.com"
                and len(path) > 1
                and path[-2] in ("articles", "read")
            ):
                return {"status": True, "base64_str": path[-1]}
            return {"status": False, "message": "Invalid Google News URL format."}
        except Exception as e:
            return {"status": False, "message": f"Error in get_base64_str: {str(e)}"}

    async def get_decoding_params(self, base64_str: str) -> dict:
        """
        Fetches signature and timestamp required for decoding from Google News.

        Tries https://news.google.com/articles/{base64_str} first,
        falls back to https://news.google.com/rss/articles/{base64_str}.

        Args:
            base64_str: The base64 string extracted from the Google News URL.

        Returns:
            dict with 'status', 'signature', 'timestamp', 'base64_str' (if success)
            or 'status' and 'message' (if failed).
        """
        # Try the first URL format.
        try:
            url = f"https://news.google.com/articles/{base64_str}"
            print(f"  [DEBUG] Trying articles URL: {url[:100]}...")
            response = await self.client.get(url)
            print(f"  [DEBUG] HTTP Status: {response.status_code}")
            print(f"  [DEBUG] Response length: {len(response.text)} chars")
            print(f"  [DEBUG] First 500 chars of response: {response.text[:500]}")
            response.raise_for_status()
            parser = HTMLParser(response.text)
            data_element = parser.css_first("c-wiz > div[jscontroller]")
            if data_element is None:
                # Fallback: Try alternative selectors
                data_element = parser.css_first("[data-n-a-sg]")
            if data_element is None:
                # Debug: Finde alle Elemente mit data-* Attributen
                all_data_elements = parser.css("[data-*]")
                print(f"  [DEBUG] No jscontroller found. Found {len(all_data_elements)} elements with data-* attributes.")
                for elem in all_data_elements[:3]:
                    print(f"    Tag: {elem.tag}, attrs: {dict(elem.attributes)}")
                return {
                    "status": False,
                    "message": "Failed to fetch data attributes from Google News with the articles URL.",
                    "_debug_html_preview": response.text[:1000],
                }
            return {
                "status": True,
                "signature": data_element.attributes.get("data-n-a-sg"),
                "timestamp": data_element.attributes.get("data-n-a-ts"),
                "base64_str": base64_str,
            }
        except httpx.RequestError as req_err:
            print(f"  [DEBUG] Request error in get_decoding_params (articles URL): {req_err}")
            print(f"  [DEBUG] Status code (if available): {getattr(getattr(req_err, 'response', None), 'status_code', 'N/A')}")
            # Fallback to RSS URL.
            try:
                url = f"https://news.google.com/rss/articles/{base64_str}"
                print(f"  [DEBUG] Trying RSS URL: {url[:100]}...")
                response = await self.client.get(url)
                print(f"  [DEBUG] HTTP Status: {response.status_code}")
                print(f"  [DEBUG] Response length: {len(response.text)} chars")
                print(f"  [DEBUG] First 500 chars of response: {response.text[:500]}")
                response.raise_for_status()
                parser = HTMLParser(response.text)
                data_element = parser.css_first("c-wiz > div[jscontroller]")
                if data_element is None:
                    # Debug: Finde alle Elemente mit data-* Attributen
                    all_data_elements = parser.css("[data-*]")
                    print(f"  [DEBUG] No jscontroller found. Found {len(all_data_elements)} elements with data-* attributes.")
                    for elem in all_data_elements[:3]:
                        print(f"    Tag: {elem.tag}, attrs: {dict(elem.attributes)}")
                    return {
                        "status": False,
                        "message": "Failed to fetch data attributes from Google News with the RSS URL.",
                        "_debug_html_preview": response.text[:1000],
                    }
                return {
                    "status": True,
                    "signature": data_element.attributes.get("data-n-a-sg"),
                    "timestamp": data_element.attributes.get("data-n-a-ts"),
                    "base64_str": base64_str,
                }
            except httpx.RequestError as rss_req_err:
                print(f"  [DEBUG] Request error in get_decoding_params (RSS URL): {rss_req_err}")
                print(f"  [DEBUG] Status code (if available): {getattr(getattr(rss_req_err, 'response', None), 'status_code', 'N/A')}")
                return {
                    "status": False,
                    "message": f"Request error in get_decoding_params with RSS URL: {str(rss_req_err)}",
                }
            except Exception as e:
                print(f"  [DEBUG] Unexpected error in get_decoding_params: {e}")
                return {
                    "status": False,
                    "message": f"Unexpected error in get_decoding_params: {str(e)}",
                }

    async def decode_url(self, signature: str, timestamp: str, base64_str: str) -> dict:
        """
        Decodes the Google News URL using the signature and timestamp.

        Args:
            signature: The signature for decoding.
            timestamp: The timestamp for decoding.
            base64_str: The base64 string from the Google News URL.

        Returns:
            dict with 'status' and 'decoded_url' (if successful)
            or 'status' and 'message' (if failed).
        """
        try:
            url = "https://news.google.com/\\_/DotsSplashUi/data/batchexecute"
            payload = [
                "Fbv4je",
                f'["garturlreq",[["X","X",["X","X"]],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],"X","X",1,[1,1,1],1,1,null,0,0,null,0],"{base64_str}",{timestamp},"{signature}"',
            ]
            headers = {
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win6; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            }
            print(f"  [DEBUG] decode_url: POST to {url}")
            print(f"  [DEBUG] decode_url: Payload (truncated): {json.dumps([[payload]])[:300]}...")
            response = await self.client.post(
                url,
                headers=headers,
                data=f"f.req={quote(json.dumps([[payload]]))}",
            )
            print(f"  [DEBUG] decode_url: HTTP Status: {response.status_code}")
            print(f"  [DEBUG] decode_url: Response length: {len(response.text)} chars")
            print(f"  [DEBUG] decode_url: First 500 chars: {response.text[:500]}")
            response.raise_for_status()
            parsed_data = json.loads(response.text.split("\n\n")[1])[:-2]
            decoded_url = json.loads(parsed_data[0][2])[1]
            return {"status": True, "decoded_url": decoded_url}
        except httpx.RequestError as req_err:
            print(f"  [DEBUG] Request error in decode_url: {req_err}")
            return {
                "status": False,
                "message": f"Request error in decode_url: {str(req_err)}",
            }
        except (json.JSONDecodeError, IndexError, TypeError) as parse_err:
            print(f"  [DEBUG] Parsing error in decode_url: {parse_err}")
            return {
                "status": False,
                "message": f"Parsing error in decode_url: {str(parse_err)}",
            }
        except Exception as e:
            print(f"  [DEBUG] Unexpected error in decode_url: {e}")
            return {"status": False, "message": f"Error in decode_url: {str(e)}"}

    async def decode_google_news_url(self, source_url: str, interval: Optional[int] = None) -> dict:
        """
        Decodes a Google News article URL into its original source URL.

        Args:
            source_url: The Google News article URL.
            interval: Delay in seconds before decoding (rate limit).

        Returns:
            dict with 'status' and 'decoded_url' (if successful)
            or 'status' and 'message' (if failed).
        """
        try:
            base64_response = self.get_base64_str(source_url)
            if not base64_response["status"]:
                return base64_response

            decoding_params_response = await self.get_decoding_params(
                base64_response["base64_str"]
            )
            if not decoding_params_response["status"]:
                return decoding_params_response

            decoded_url_response = await self.decode_url(
                decoding_params_response["signature"],
                decoding_params_response["timestamp"],
                decoding_params_response["base64_str"],
            )
            if interval:
                await asyncio.sleep(interval)
            return decoded_url_response
        except Exception as e:
            return {
                "status": False,
                "message": f"Error in decode_google_news_url: {str(e)}",
            }

    async def close(self):
        await self.client.aclose()
