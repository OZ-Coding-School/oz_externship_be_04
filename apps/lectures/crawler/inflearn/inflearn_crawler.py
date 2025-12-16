import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, cast

import httpx

from apps.core.logger.logging import get_logger

logger = get_logger(__name__)
JsonDict = Dict[str, Any]


class InflearnCrawler:
    LIST_API = "https://course-api.inflearn.com/client/api/v2/courses/search"
    META_API = "https://course-api.inflearn.com/client/api/v1/course/{cid}/meta?lang=ko"
    PAYMENT_API = "https://course-api.inflearn.com/client/api/v1/courses/{cid}/payment-info?lang=ko"
    REVIEW_API = "https://ucc-api.inflearn.com/client/api/v1/reviews/course/{cid}"

    PAGE_SIZE = 40
    REVIEW_PARAMS = {
        "pageNumber": 1,
        "pageSize": 4,
        "sort": "RECENT",
        "lang": "ko",
    }

    PARAMS_BASE = {
        "keyword": "",
        "categories": "",
        "isBot": "false",
        "isDiscounted": "false",
        "isEarlybirdDiscounted": "false",
        "pageSize": PAGE_SIZE,
        "sort": "POPULAR",
        "types": "ONLINE,OFFLINE",
        "lang": "ko",
        "uri": "https://www.inflearn.com/",
        "referrerUri": "https://www.inflearn.com/",
    }

    auto_category_id = 1

    def normalize_level(self, code: str) -> str:
        code = code.upper()
        if "BEGINNER" in code or "BASIC" in code:
            return "EASY"
        if "INTERMEDIATE" in code:
            return "NORMAL"
        if "ADVANCED" in code or "HIGH" in code:
            return "HARD"
        return ""

    def next_category(self, name: str) -> Dict[str, Any]:
        return {"name": name}

    async def _get(
        self, client: httpx.AsyncClient, url: str, params: Optional[Dict[str, Any]] = None
    ) -> Optional[JsonDict]:
        try:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                return cast(JsonDict, resp.json())
        except Exception:
            return None
        return None

    async def _fetch_list_page(self, client: httpx.AsyncClient, page: int) -> Optional[JsonDict]:
        params = {**self.PARAMS_BASE, "pageNumber": page}
        return await self._get(client, self.LIST_API, params)

    async def _fetch_meta(self, client: httpx.AsyncClient, cid: int) -> Optional[JsonDict]:
        return await self._get(client, self.META_API.format(cid=cid))

    async def _fetch_payment(self, client: httpx.AsyncClient, cid: int) -> Optional[JsonDict]:
        return await self._get(client, self.PAYMENT_API.format(cid=cid))

    async def _fetch_reviews(self, client: httpx.AsyncClient, cid: int) -> List[JsonDict]:
        data = await self._get(client, self.REVIEW_API.format(cid=cid), self.REVIEW_PARAMS)
        out: List[JsonDict] = []
        if not data or "data" not in data:
            return out
        items = data["data"].get("items", [])
        for i, r in enumerate(items, start=1):
            rating = r.get("star")
            content = r.get("body")
            if not rating or not content or content.strip() == "":
                continue
            out.append(
                {
                    "id": f"{cid}_{i}",
                    "rating": rating,
                    "content": content,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
        return out

    def extract_tags(self, meta: Optional[JsonDict]) -> List[str]:
        if not meta or "data" not in meta:
            return []
        data = meta["data"]
        tags_set = set()

        tags = data.get("tags")
        if isinstance(tags, list):
            for tg in tags:
                name = tg.get("name")
                if name:
                    tags_set.add(name)

        tag_groups = data.get("tagGroups")
        if isinstance(tag_groups, list):
            for group in tag_groups:
                tg_list = group.get("tags")
                if isinstance(tg_list, list):
                    for tg in tg_list:
                        name = tg.get("name")
                        if name:
                            tags_set.add(name)

        return list(tags_set)

    async def _gather_details(self, client: httpx.AsyncClient, cid: int, slug: str, base: JsonDict) -> JsonDict:
        meta = await self._fetch_meta(client, cid)
        payment = await self._fetch_payment(client, cid)
        reviews = await self._fetch_reviews(client, cid)

        instructor = ""
        difficulty = ""

        tag_names = self.extract_tags(meta)
        categories: List[Dict[str, Any]] = []

        if tag_names:
            for name in tag_names:
                categories.append(self.next_category(name))
        else:
            if payment and payment.get("data"):
                pdata = payment["data"]
                cat = pdata.get("category")
                if cat:
                    main = cat.get("main")
                    sub = cat.get("sub")

                    if main and main.get("title"):
                        categories.append(self.next_category(main["title"]))

                    if sub and sub.get("title"):
                        categories.append(self.next_category(sub["title"]))

        if payment and payment.get("data"):
            pdata = payment["data"]

            ins = pdata.get("instructors")
            if ins:
                instructor = ins[0].get("name", "")

            levels = pdata.get("levels")
            if levels:
                for lvl in levels:
                    if lvl.get("isActive"):
                        difficulty = self.normalize_level(str(lvl.get("code", "")))

        payinfo = payment["data"].get("paymentInfo") if payment and payment.get("data") else None
        original_price = payinfo.get("regularPrice") if payinfo else 0
        discounted_price = payinfo.get("payPrice") if payinfo else 0

        return {
            "id": cid,
            "title": base["title"],
            "instructor": instructor,
            "total_class_time": base["total_class_time"],
            "original_price": original_price,
            "discounted_price": discounted_price,
            "difficulty": difficulty,
            "thumbnail_img_url": base["thumbnail_img_url"],
            "average_rating": base["average_rating"],
            "platform": "INFLEARN",
            "url_link": f"https://www.inflearn.com/course/{slug}",
            "categories": categories,
            "reviews": reviews,
        }

    async def get_all_courses(self) -> List[JsonDict]:
        async with httpx.AsyncClient(http2=True, timeout=30) as client:
            first = await self._fetch_list_page(client, 1)
            if not first or "data" not in first:
                return []

            total = first["data"]["totalPage"]
            fetched_pages = await asyncio.gather(*[self._fetch_list_page(client, p) for p in range(2, total + 1)])

            pages = [first] + [pg for pg in fetched_pages if pg is not None]
            items: List[tuple[int, str, JsonDict]] = []

            for pg in pages:
                for item in pg["data"].get("items", []):
                    info = item.get("course") or {}
                    cid = info.get("id")
                    slug = info.get("slug")
                    if not cid or not slug:
                        continue
                    base = {
                        "title": info.get("title"),
                        "thumbnail_img_url": info.get("thumbnailUrl"),
                        "total_class_time": info.get("runtimeSecond", 0) // 60,
                        "average_rating": round(float(info.get("star") or 0), 2),
                    }
                    items.append((cid, slug, base))

            return await asyncio.gather(*[self._gather_details(client, cid, slug, base) for cid, slug, base in items])
