import asyncio
import hashlib
import random
from datetime import datetime, timezone
import httpx
from .config import settings
from . import db
from .knowledge import sitemap_urls, parse_article, chunk_sections, embed_chunks, content_hash, utcnow

async def polite_sleep():
    await asyncio.sleep(settings.request_delay_seconds)

async def fetch(client: httpx.AsyncClient, url: str, semaphore: asyncio.Semaphore, attempts=3):
    last_error=None
    for attempt in range(1,attempts+1):
        try:
            async with semaphore:
                await polite_sleep()
                response=await client.get(url, timeout=settings.request_timeout_seconds)
                response.raise_for_status()
                return response
        except (httpx.TimeoutException,httpx.NetworkError,httpx.HTTPStatusError) as exc:
            last_error=str(exc)
            if isinstance(exc,httpx.HTTPStatusError) and exc.response.status_code < 500 and exc.response.status_code != 429:
                break
            await asyncio.sleep(min(2 ** (attempt-1) + random.random(), 10))
    raise RuntimeError(last_error or "Fetch failed")

async def run_ingestion():
    run_id=db.run_start()
    added=updated=removed=failed=0
    details={"errors":[]}
    semaphore=asyncio.Semaphore(max(1,settings.max_concurrency))
    headers={"User-Agent":settings.user_agent}
    async with httpx.AsyncClient(headers=headers,follow_redirects=True) as client:
        sitemap_response=await fetch(client,settings.sitemap_url,semaphore)
        pages=sitemap_urls(sitemap_response.text)
        current_urls={p["url"] for p in pages}
        previous_urls=db.active_urls()
        for page in pages:
            url=page["url"]
            try:
                old=db.get_article(url)
                # lastmod is a useful hint, but fetch/hash content to catch sites with missing/stale lastmod.
                response=await fetch(client,url,semaphore)
                parsed=parse_article(response.text,url)
                digest=content_hash(parsed["content"])
                if old and old["content_hash"]==digest and old["active"]:
                    db.manifest_update(url,"unchanged",0,None)
                    continue
                chunks=chunk_sections(parsed["sections"])
                chunks=embed_chunks(chunks)
                db.save_article(url,parsed["title"],parsed["content"],digest,page.get("last_modified"),utcnow())
                db.replace_chunks(url,chunks)
                db.manifest_update(url,"processed",1,None)
                if old and old["active"]:
                    updated+=1
                else:
                    added+=1
            except Exception as exc:
                failed+=1
                db.manifest_update(url,"failed",1,str(exc)[:1000])
                details["errors"].append({"url":url,"error":str(exc)[:300]})
        removed_urls=previous_urls-current_urls
        db.mark_removed(removed_urls)
        run_status="completed" if failed==0 else "completed_with_errors"
        db.run_finish(run_id,status=run_status,discovered=len(pages),added=added,updated=updated,
                      removed=len(removed_urls),failed=failed,details=details)
        return {"run_id":run_id,"status":run_status,"discovered":len(pages),"added":added,
                "updated":updated,"removed":len(removed_urls),"failed":failed,"errors":details["errors"]}

def run_ingestion_sync():
    return asyncio.run(run_ingestion())
