import asyncio
import json
import time
from typing import Any, Dict, List, Mapping, Sequence, Union, cast
from urllib.parse import quote

import httpx
from httpx import Limits

from apps.core.logger.logging import get_logger

Params = Mapping[str, str | int | float | bool | None | Sequence[str | int | float | bool | None]]
logger = get_logger(__name__)


class InflearnCrawler:
    COURSE_LIST_API = "https://course-api.inflearn.com/client/api/v1/course/search"
    REVIEW_API = "https://ucc-api.inflearn.com/client/api/v1/reviews/course/{course_id}"

    page_size: int = 100
    max_concurrent: int = 10
    review_concurrent = 10

    review_params: Params = {
        "pageNumber": 1,
        "pageSize": 4,
        "sort": "RECOMMEND",
        "lang": "ko",
    }

    rating_map = {
        5: 5,
        4: 4,
        3: 3,
        2: 2,
        1: 1,
    }

    async def get_all_courses(self) -> List[Dict[str, Any]]:
        logger.info(f"인프런 전체 강의 크롤링 시작")

        async with httpx.AsyncClient(
            timeout=20.0, http2=True, limits=Limits(max_connections=200, max_keepalive_connections=200)
        ) as client:
            total_pages = await self._get_total_pages(client)
            logger.info(f"총 페이지 수: {total_pages}")

            if total_pages == 0:
                logger.warning("total_pages == 0")
                return []

            all_raw_items = await self._get_all_course_items(client, total_pages)
            logger.info(f" 총{len(all_raw_items)}개 수집")

            course_dict: Dict[int, Dict[str, Any]] = {}
            for item in all_raw_items:
                course_id = item.get("course", {}).get("id")
                if course_id:
                    course_dict[course_id] = item

            review_dict = await self._get_reviews_for_all(client, list(course_dict.keys()))
            logger.info("리뷰 완료")

            final_results = self._combine(course_dict, review_dict)
            logger.info(f"강의 데이터 생성: {len(final_results)}개")
            return final_results

    async def _get_total_pages(self, client: httpx.AsyncClient) -> int:
        params: Params = cast(
            Params,
            {
                "pageNumber": 1,
                "pageSize": self.page_size,
                "sort": "POPULAR",
                "lang": "ko",
            },
        )

        try:
            res = await client.get(self.COURSE_LIST_API, params=params)
            res.raise_for_status()
            data = res.json()
            return cast(int, data.get("data", {}).get("totalPage", 1))
        except Exception as e:
            logger.error(f"총 페이지 계산 실패 params={params}", exc_info=True)
            return 0

    async def _get_all_course_items(self, client: httpx.AsyncClient, total_pages: int) -> List[Dict[str, Any]]:

        base_params: Params = cast(
            Params,
            {
                "pageSize": self.page_size,
                "sort": "POPULAR",
                "lang": "ko",
            },
        )

        tasks: List[asyncio.Task[List[Dict[str, Any]]]] = []

        for page_num in range(1, total_pages + 1):
            logger.info(f"페이지 요청중: {page_num}/{total_pages}")

            params: Params = cast(
                Params,
                {**base_params, "pageNumber": page_num},
            )
            tasks.append(asyncio.create_task(self._fetch_course_page(client, params)))

        collected: List[Dict[str, Any]] = []

        for i in range(0, len(tasks), self.max_concurrent):
            batch = tasks[i : i + self.max_concurrent]
            results = await asyncio.gather(*batch, return_exceptions=True)

            for items in results:
                if isinstance(items, Exception):
                    logger.error("페이지 수집 중 오류", exc_info=True)
                elif isinstance(items, list):
                    collected.extend(items)
        return collected

    async def _fetch_course_page(self, client: httpx.AsyncClient, params: Params) -> List[Dict[str, Any]]:
        try:
            res = await client.get(self.COURSE_LIST_API, params=params)
            res.raise_for_status()
            return cast(List[Dict[str, Any]], res.json().get("data", {}).get("items", []))
        except Exception:
            logger.error(f"강의 페이지 요청 불가 params={params}", exc_info=True)
            return []

    async def _get_reviews_for_all(
        self, client: httpx.AsyncClient, course_ids: List[int]
    ) -> Dict[int, List[Dict[str, Any]]]:
        logger.info(f"리뷰 수집 시작 (총 {len(course_ids)}개")
        tasks: List[asyncio.Task[Dict[str, Any]]] = []

        for cid in course_ids:
            tasks.append(asyncio.create_task(self._fetch_single_course_reviews(client, cid)))

        review_dict: Dict[int, List[Dict[str, Any]]] = {}

        for i in range(0, len(tasks), self.max_concurrent):
            batch = tasks[i : i + self.max_concurrent]
            results = await asyncio.gather(*batch, return_exceptions=True)
            for item in results:
                if isinstance(item, dict) and item.get("course_id"):
                    review_dict[item["course_id"]] = item["reviews"]

        return review_dict

    async def _fetch_single_course_reviews(self, client: httpx.AsyncClient, course_id: int) -> Dict[str, Any]:
        try:
            url = self.REVIEW_API.format(course_id=course_id)
            res = await client.get(url, params=self.review_params)
            res.raise_for_status()

            items = res.json().get("data", {}).get("items", [])
            rv_list = []

            for rv in items:
                rv_list.append({"rating": self.rating_map.get(rv.get("star"), 0), "content": rv.get("body", "")})

            return {"course_id": course_id, "reviews": rv_list}
        except Exception:
            logger.error(f"리뷰 요청 실패: {course_id}", exc_info=True)
            return {"course_id": course_id, "reviews": []}

    def _combine(
        self,
        course_dict: Dict[int, Dict[str, Any]],
        review_dict: Dict[int, List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:

        final_list = []

        for cid, raw in course_dict.items():
            info = raw.get("course", {})

            level_map = {
                "BEGINNER": "EASY",
                "INTERMEDIATE": "NORMAL",
                "ADVANCED": "HARD",
            }

            label_map = {
                "EASY": "초급",
                "NORMAL": "중급",
                "HARD": "어려움",
            }

            difficulty_raw = info.get("difficulty")
            difficulty_enum = level_map.get(difficulty_raw, "NORMAL")
            difficulty_label = label_map.get(difficulty_enum, "중급")

            try:
                merged = {
                    "id": cid,
                    "title": info.get("title"),
                    "instructor": raw.get("course", {}).get("instructor", {}).get("name"),
                    "total_class_time": info.get("runtimeSecond", 0) // 60,
                    "original_price": info.get("price", {}).get("base", 0),
                    "discounted_price": info.get("price", {}).get("discounted", 0),
                    "difficulty": difficulty_enum,
                    "difficulty_label": difficulty_label,
                    "thumbnail_img_url": quote(info.get("thumbnailUrl"), safe=":/"),
                    "average_rating": float(info.get("star") or 0),
                    "platform": "INFLEARN",
                    "url_link": f"https://www.inflearn.com/course/{info.get('slug')}",
                    "categories": [
                        {"id": c.get("id"), "name": c.get("title")}
                        for c in info.get("metadata", {}).get("categories", [])
                    ],
                    "reviews": [
                        {
                            "id": idx + 1,
                            "rating": rv.get("rating"),
                            "content": rv.get("content"),
                            "created_at": rv.get("created_at", None),
                        }
                        for idx, rv in enumerate(review_dict.get(cid, []))
                    ],
                }

                final_list.append(merged)

            except Exception:
                logger.error(f"병합 오류: course_id={cid}", exc_info=True)

        return final_list


async def main() -> None:
    start = time.time()
    crawler = InflearnCrawler()
    data = await crawler.get_all_courses()
    end = time.time()

    logger.info(f"총 강의 수: {len(data)}개")
    logger.info(f"총 실행 시간: {end - start:.1f}초")
    print(json.dumps(data[:4], indent=4, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
