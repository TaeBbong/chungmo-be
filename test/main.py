import requests
from bs4 import BeautifulSoup
from typing import Set
import re


def contains_korean(text: str) -> bool:
    return bool(re.search(r'[\uac00-\ud7a3]', text))


def fetch_html(url: str) -> str:
    """지정된 URL에서 HTML을 가져옵니다."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error: Failed to fetch the page. {e}")
        return ""


def extract_text_content(soup: BeautifulSoup, content_set: Set[str]) -> None:
    """본문 텍스트 콘텐츠를 추출하여 content_set에 추가합니다."""
    # content_set.add(soup.get_text())
    for element in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "div", "script", "meta", "title"]):
        text = element.get_text(strip=True)
        if text and len(text) >= 2 and contains_korean(text):  # 너무 짧은 텍스트 필터링
            content_set.add(text)


def extract_media_content(soup: BeautifulSoup, content_set: Set[str]) -> None:
    """이미지 및 링크 콘텐츠를 추출하여 content_set에 추가합니다."""
    for img in soup.find_all("img"):
        if src := img.get("src"):
            content_set.add(f"[IMAGE] {src}")

    for link in soup.find_all("link"):
        if href := link.get("href"):
            content_set.add(f"[LINK] {href}")

    for anchor in soup.find_all("a"):
        href = anchor.get("href", "").strip()
        text = anchor.get_text(strip=True)
        if href:
            content_set.add(f"[ANCHOR] {text} → {href}" if text else f"[ANCHOR] {href}")


def extract_content_with_images(url: str) -> None:
    """주어진 URL에서 텍스트와 미디어 콘텐츠를 추출하여 출력합니다."""
    html = fetch_html(url)
    if not html:
        return

    soup = BeautifulSoup(html, "html.parser")

    # 불필요한 태그 제거
    for tag in soup(["style", "noscript", "link"]):
        tag.decompose()

    extracted_content: Set[str] = set()

    extract_text_content(soup, extracted_content)
    extract_media_content(soup, extracted_content)

    # 정렬된 리스트 출력
    print("\n".join(sorted(extracted_content)))


if __name__ == "__main__":
    # URL = "https://ourfirstletter.com/w/250405-PSYYv4"
    # URL = "https://mcard.cryucard.com/c/JjJ9DKvEsmYtOHk5VkZl"
    URL = "https://toourguest.com/cards/sohyeondongyeob"
    html = fetch_html(URL)
    # print(html)
    extract_content_with_images(URL)
