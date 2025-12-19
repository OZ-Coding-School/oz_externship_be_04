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
        "pageSize": 30,
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

    def normalize_level(self, code: str) -> str:
        code = code.upper()
        if "BEGINNER" in code or "BASIC" in code:
            return "EASY"
        if "INTERMEDIATE" in code:
            return "NORMAL"
        if "ADVANCED" in code or "HIGH" in code:
            return "HARD"
        return ""

    # 카테고리
    def next_category(self, name: str) -> Dict[str, Any]:
        return {"name": name}

    # 공통 get 요청
    async def _get(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[JsonDict]:
        try:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                return cast(JsonDict, resp.json())
            # 비정상 응답시
            logger.warning(f"응답 코드 {resp.status_code}: {url}")
        except Exception as e:
            # 네트워크 오류 시
            logger.warning(f"GET 실패: {url} | {e}")
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
        # 응답, 데이터 키 없으면 빈 값
        if not data or "data" not in data:
            return out
        # 리뷰가 여러개라서 평점과 내용 값 추출을 위한 순회
        items = data["data"].get("items", [])
        for i, r in enumerate(items, start=1):
            rating = r.get("star")
            content = r.get("body")
            # 내용 없으면 스킵
            if not rating or not content or content.strip() == "":
                continue
            out.append(
                {
                    "id": r.get("id"),  # 리뷰 api에서 제공하는 id사용
                    "rating": rating,
                    "content": content,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            if len(out) == 4:  # 평점과 바디에 있는 4개만 가져옴
                break
        return out

    # 태그 추출
    def extract_tags(self, meta: Optional[JsonDict]) -> List[str]:
        if not meta or "data" not in meta:
            return []

        data = meta["data"]
        tags_set = set()
        # 1차
        tags = data.get("tags")
        if isinstance(tags, list):
            for tg in tags:
                name = tg.get("name")
                if name:
                    tags_set.add(name)
        # 2차
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

    # 강의 상세 수집
    async def _gather_details(
        self,
        client: httpx.AsyncClient,
        cid: int,
        slug: str,
        base: JsonDict,
    ) -> JsonDict:
        # 정보, 결제, 리뷰 병렬 수집
        meta, payment, reviews = await asyncio.gather(
            self._fetch_meta(client, cid),
            self._fetch_payment(client, cid),
            self._fetch_reviews(client, cid),
        )

        instructor = ""
        difficulty = ""
        # 태그 기반 카테고리 우선
        tag_names = self.extract_tags(meta)
        categories: List[Dict[str, Any]] = []

        if tag_names:
            for name in tag_names:
                categories.append(self.next_category(name))
        else:
            # 없으면 결제 정보 카테고리 사용
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
        # 강사명, 난이도 수집
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
        # 가격 정보
        payinfo = payment["data"].get("paymentInfo") if payment and payment.get("data") else None
        original_price = payinfo.get("regularPrice") if payinfo else 0
        discount_price = payinfo.get("payPrice") if payinfo else 0

        return {
            "id": cid,
            "title": base["title"],
            "instructor": instructor,
            "total_class_time": base["total_class_time"],
            "original_price": original_price,
            "discount_price": discount_price,
            "difficulty": difficulty,
            "thumbnail_img_url": base["thumbnail_img_url"],
            "average_rating": base["average_rating"],
            "platform": "INFLEARN",
            "url_link": f"https://www.inflearn.com/course/{slug}",
            "categories": categories,
            "reviews": reviews,
        }

    # 전체 강의 수집
    async def get_all_courses(self) -> List[JsonDict]:
        # 페이지 최대 20, 상세 최대 10개
        limits = httpx.Limits(max_connections=20, max_keepalive_connections=10)
        timeout = httpx.Timeout(10.0, connect=5.0)

        async with httpx.AsyncClient(
            http2=True,
            limits=limits,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (crawler; contact=admin@yourapp.com)"},
        ) as client:
            # 1페이지 요청 후 전체 페이지 수 확인
            first = await self._fetch_list_page(client, 1)
            if not first or "data" not in first:
                return []

            total = first["data"]["totalPage"]
            fetched_pages: List[JsonDict] = []
            # 페이지 10개 단위로 병렬
            for start in range(2, total + 1, 10):
                chunk = range(start, min(start + 10, total + 1))
                chunk_pages = await asyncio.gather(*[self._fetch_list_page(client, p) for p in chunk])
                fetched_pages.extend(pg for pg in chunk_pages if pg)
            # 페이지 합침
            all_pages: List[JsonDict] = []
            for pg in [first, *fetched_pages]:
                if pg is None:
                    continue
                all_pages.append(pg)
            # 강의 기본 정보
            items: List[tuple[int, str, JsonDict]] = []

            for pg in all_pages:
                for item in pg["data"].get("items", []):
                    info = item.get("course") or {}
                    cid = info.get("id")
                    slug = info.get("slug")
                    if not cid or not slug:
                        continue

                    base = {
                        "title": info.get("title"),
                        "thumbnail_img_url": info.get("thumbnailUrl"),
                        "total_class_time": (info.get("runtimeSecond", 0) or 0) // 60,
                        "average_rating": round(float(info.get("star") or 0), 2),
                    }
                    items.append((cid, slug, base))

            sem = asyncio.Semaphore(10)

            async def limited_gather(
                cid: int,
                slug: str,
                base: JsonDict,
            ) -> JsonDict:
                async with sem:
                    return await self._gather_details(client, cid, slug, base)

            results: list[JsonDict] = await asyncio.gather(
                *[limited_gather(cid, slug, base) for cid, slug, base in items]
            )

            return results
