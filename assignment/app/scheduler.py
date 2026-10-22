import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .config import settings
from .ingestion import run_ingestion
from .main import app
import uvicorn

async def main():
    scheduler=AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(run_ingestion,"cron",hour=settings.refresh_hour_utc,minute=0,
                      id="daily-knowledge-refresh",replace_existing=True,max_instances=1)
    scheduler.start()
    config=uvicorn.Config(app,host="0.0.0.0",port=8000)
    server=uvicorn.Server(config)
    await server.serve()

if __name__=="__main__":
    asyncio.run(main())
