import asyncio
import json
import time
from typing import Any, Dict, List, Union, cast
from urllib.parse import quote

import httpx

Params = Dict[str, Union[str, int, float, bool, None]]  # mypy 대용


class InflearnCrawler:
    COURSE_LIST_API = "https://course-api.inflearn.com/client/api/v1/course/search"
    REVIEW_API = "https://ucc-api.inflearn.com/client/api/v1/reviews/course/{course_id}"

    page_size: int = 100  # 페이지당 가져올 강의 수
    max_concurrent: int = 10  # 동시 요청 수 15로 했다가 튕김

    async def get_all_courses(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            total_pages = await self._get_total_pages(client)
            if total_pages == 0:
                return []

            all_raw_items = await self._get_all_course_items(client, total_pages)  # 강의 가져오기

            course_dict: Dict[int, Dict[str, Any]] = {}
            for item in all_raw_items:
                course_id = item.get("course", {}).get("id")  # 키 값
                if course_id:
                    course_dict[course_id] = item  # 벨류 값

            review_dict = await self._get_reviews_for_all(client, list(course_dict.keys()))  # 리뷰 4개
            final_results = self._combine(course_dict, review_dict)
            return final_results

    async def _get_total_pages(self, client: httpx.AsyncClient) -> int:
        params: Params = {
            "pageNumber": 1,
            "pageSize": self.page_size,
            "sort": "POPULAR",  # 인기순 이게 가장 빠르다고합니다
            "lang": "ko",
        }

        try:
            res = await client.get(self.COURSE_LIST_API, params=params)
            res.raise_for_status()
            data = res.json()
            return cast(int, data.get("data", {}).get("totalPage", 1))
        except Exception:
            return 0

    async def _get_all_course_items(self, client: httpx.AsyncClient, total_pages: int) -> List[Dict[str, Any]]:

        base_params: Params = {
            "pageSize": self.page_size,
            "sort": "POPULAR",
            "lang": "ko",
        }

        tasks: List[asyncio.Task[List[Dict[str, Any]]]] = []

        for page_num in range(1, total_pages + 1):
            params: Params = {**base_params, "pageNumber": page_num}
            tasks.append(asyncio.create_task(self._fetch_course_page(client, params)))

        collected_items: List[Dict[str, Any]] = []

        for i in range(0, len(tasks), self.max_concurrent):
            batch = tasks[i : i + self.max_concurrent]
            results = await asyncio.gather(*batch, return_exceptions=True)
            for page_items in results:
                if isinstance(page_items, list):
                    collected_items.extend(page_items)

        return collected_items

    async def _fetch_course_page(self, client: httpx.AsyncClient, params: Params) -> List[Dict[str, Any]]:
        try:
            res = await client.get(self.COURSE_LIST_API, params=params)
            res.raise_for_status()
            data = res.json().get("data", {}).get("items", [])
            return cast(List[Dict[str, Any]], data)
        except Exception:
            return cast(List[Dict[str, Any]], [])

    async def _get_reviews_for_all(
        self, client: httpx.AsyncClient, course_ids: List[int]
    ) -> Dict[int, List[Dict[str, Any]]]:
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

        params: Params = {
            "pageNumber": 1,
            "pageSize": 4,
            "sort": "RECOMMEND",
            "lang": "ko",
        }

        rating_text: Dict[int, str] = {
            5: "5_OUT_OF_5_STARS",
            4: "4_OUT_OF_5_STARS",
            3: "3_OUT_OF_5_STARS",
            2: "2_OUT_OF_5_STARS",
            1: "1_OUT_OF_5_STARS",
        }

        try:
            url = self.REVIEW_API.format(course_id=course_id)
            res = await client.get(url, params=params)
            res.raise_for_status()

            items = res.json().get("data", {}).get("items", [])
            rv_list: List[Dict[str, Any]] = []

            for rv in items:
                score = rating_text.get(rv.get("star"))
                rv_list.append({"rating": score, "content": rv.get("body", "")})

            return {"course_id": course_id, "reviews": rv_list}
        except Exception:
            return {"course_id": course_id, "reviews": []}

    def _combine(
        self,
        course_dict: Dict[int, Dict[str, Any]],
        review_dict: Dict[int, List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:

        final_list: List[Dict[str, Any]] = []

        for cid, raw in course_dict.items():
            info = raw.get("course", {})

            merged = {
                "id": cid,
                "title": info.get("title"),
                "slug": info.get("slug"),
                "instructor": raw.get("instructor", {}).get("name"),
                "rating": info.get("star"),
                "duration_min": info.get("runtimeSecond", 0) // 60,
                "description": info.get("description", "").replace("\n", " "),
                "thumbnail": quote(info.get("thumbnailUrl"), safe=":/?&"),
                "url": f"https://www.inflearn.com/course/{info.get('slug')}",
                "categories": [
                    x.get("title") for x in info.get("metadata", {}).get("categories", []) if x.get("title")
                ],
                "reviews": review_dict.get(cid, []),
            }

            final_list.append(merged)

        return final_list


async def main() -> None:
    start = time.time()  # 시작시간
    crawler = InflearnCrawler()
    data = await crawler.get_all_courses()
    end = time.time()  # 끝시간

    print(f"총 강의 수: {len(data)}개")
    print(f"총 실행 시간: {end - start:.2f}초")
    print(json.dumps(data[0], indent=4, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
