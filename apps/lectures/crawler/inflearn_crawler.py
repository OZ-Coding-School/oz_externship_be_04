import asyncio
import json
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List

from playwright.async_api import (
    Browser,
    BrowserContext,
    Locator,
    Page,
    async_playwright,
)

from apps.core.utils.base62 import Base62


async def safe_text(locator: Locator, index: int = 0) -> str:
    if await locator.count() > index:
        return (await locator.nth(index).inner_text()).strip()
    return ""


async def crawl_inflearn_minimal(keyword: str, limit: int = 10) -> List[Dict[str, Any]]:  # mypy에 막혔음
    results: List[Dict[str, Any]] = []
    now: str = datetime.now().strftime("%Y-%m-%d %H:%M")

    async with async_playwright() as p:
        browser: Browser = await p.chromium.launch(headless=False)
        context: BrowserContext = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                " AppleWebKit/537.36 (KHTML, like Gecko)"
                " Chrome/120.0.0.0 Safari/537.36"
            ),  # 403 방지 우회용
            locale="ko-KR",
        )

        await context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """
        )  # 탐지 회피용

        page: Page = await context.new_page()  # chromium 새탭 열기

        page_num: int = 1  # 시작 페이지

        while len(results) < limit:
            search_url: str = (
                f"https://www.inflearn.com/courses?search={keyword}&page={page_num}"  # 키워드와 페이지 번호로 검색
            )
            await page.goto(search_url, timeout=60000)
            await page.wait_for_timeout(2000)  # 2초 대기

            cards: Locator = page.locator('a[href*="/course/"]')  # 신형

            if await cards.count() == 0:
                cards = page.locator("article.mantine-Paper-root.mantine-Card-root")  # 구형

            count: int = await cards.count()  # 강의 수량 확인

            if count == 0:
                print(f"[{keyword}] {page_num}페이지에서 강의를 찾지 못했습니다.")
                break

            for i in range(count):
                if len(results) >= limit:
                    break

                card: Locator = cards.nth(i)

                title: str = await safe_text(card.locator("p"), 0)
                instructor: str = await safe_text(card.locator("p"), 1)  # <p>태그중 0은 강의, 1은 강사

                try:
                    card_text: str = await card.inner_text()
                    rating_match = re.search(r"(\d\.\d)", card_text)  # 별점 (숫자.숫자)의 형태 찾기
                    average_rating: float = float(rating_match.group(1)) if rating_match else 0.0
                except Exception:
                    average_rating = 0.0

                img: Locator = card.locator("img")
                thumbnail_img_url: str = (await img.first.get_attribute("src")) or "" if await img.count() > 0 else ""

                href: str = (await card.get_attribute("href")) or ""
                url_link: str = (
                    href if href.startswith("http") else "https://www.inflearn.com" + href
                )  # 상대경로면 절대경로로 변환 이거 안하면 같은 url 중복 생성됨

                match = re.search(r"-(\d+)$", url_link)
                if match:
                    external_id: str | int = int(match.group(1))  # 있으면 사용
                else:
                    url_uuid: uuid.UUID = uuid.uuid5(uuid.NAMESPACE_URL, url_link)
                    external_id = Base62.uuid_encode(
                        url_uuid, length=10
                    )  # 없으면 url기반으로 uuid생성, base62로 바꿔서 id넣음

                crawler_unique_id: str = str(uuid.uuid4())  # 크롤링 데이터 마다 별도로 부여

                results.append(
                    {
                        "external_id": external_id,
                        "title": title,
                        "instructor": instructor,
                        "average_rating": average_rating,
                        "total_class_time": 0,
                        "difficulty": "NORMAL",
                        "description": "",
                        "original_price": 0,
                        "discount_price": 0,
                        "platform": "INFLEARN",
                        "url_link": url_link,
                        "thumbnail_img_url": thumbnail_img_url,
                        "created_at": now,
                        "updated_at": now,
                        "uuid": crawler_unique_id,
                    }
                )

            page_num += 1  # 페이지 넘김

        await browser.close()

    return results


if __name__ == "__main__":
    data: List[Dict[str, Any]] = asyncio.run(crawl_inflearn_minimal("파이썬", limit=10))
    print(json.dumps(data, ensure_ascii=False, indent=4))  # 결과값 json형태로 출력
