import asyncio
from typing import Any, Dict, List

from apps.lectures.crawler.inflearn.inflearn_crawler import InflearnCrawler
from apps.lectures.services.db_sync import SyncResult, sync_inflearn_db


def run_inflearn_sync() -> int:
    crawler = InflearnCrawler()
    data: List[Dict[str, Any]] = asyncio.run(crawler.get_all_courses())
    result: SyncResult = sync_inflearn_db(data)
    return result["created_lectures"] + result["updated_lectures"]
