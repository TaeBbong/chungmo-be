# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn
# from firebase_admin import initialize_app, credentials
from openai import OpenAI
import os, json, requests
from datetime import datetime
from bs4 import BeautifulSoup
from typing import Set
import re


@https_fn.on_request(secrets=["OPENAI_API_KEY"])
def test_handler(req: https_fn.Request) -> https_fn.Response:
    """테스트 데이터(JSON str)를 반환하는 API 핸들러"""
    sample_data = '''{
        "thumbnail": "https://img.freepik.com/free-vector/bride-groom-getting-married-illustration_23-2148404918.jpg?semt=ais_hybrid",
        "groom": "김철수",
        "bride": "이영희",
        "datetime": "2025-05-25T11:00:00",
        "location": "청모호텔 메인홀, 서울 강남구 일원동1가 12-34"
    }'''

    if req.method == "OPTIONS":
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
            "Access-Control-Max-Age": "3600",
        }
        return ("", 204, headers)
    headers = {"Access-Control-Allow-Origin": "*"}
    return https_fn.Response(json.dumps(sample_data), status=200, mimetype="application/json", headers=headers)


@https_fn.on_request(secrets=["OPENAI_API_KEY"])
def parse_voucher_handler(req: https_fn.Request) -> https_fn.Response:
    """POST로 link 데이터를 전달받아 html 파싱, gpt를 통해 적절한 데이터 추출 및 JSON(str)을 반환하는 API 핸들러"""
    if req.method == "OPTIONS":
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
            "Access-Control-Max-Age": "3600",
        }

        return ("", 204, headers)
    
    headers = {"Access-Control-Allow-Origin": "*"}

    try:
        data = req.get_json()
        if not isinstance(data, dict):
            return https_fn.Response(
                "Invalid request body. Expected JSON object.", 
                status=400,
                headers=headers
            )

        OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

        voucher = data.get("link")
        
        if not voucher.startswith("http"):
            return https_fn.Response(
                f"Invalid 'voucher' format. Expected a link starts with http or https.\n{voucher}", 
                status=400,
                headers=headers
            )

        parsed_result = extract_content_with_images(voucher)
        
        query = parsed_result + "\n\n"
        query += '''
        Extract the required wedding data from the given text and return it in pure JSON format, without any additional text or snippet tags. Ensure that the output follows this exact JSON structure:

        {
            "thumbnail": "",
            "groom": "", 
            "bride": "", 
            "datetime": "", // ex: 2025-04-26T14:00:00
            "location": ""
        }

        Do not include any explainations, comments, or extra characters. Only return valid JSON because I want to run following scripts after your response.
        data = response.json()
        jdata = json.loads(data)
         '''
        client = OpenAI(api_key=OPENAI_API_KEY)
        model = "gpt-4o-mini"
        messages = [{
            "role": "system",
            "content": "Parse the wedding voucher data into JSON format."
        }, {
            "role": "user",
            "content": query
        }]

        # GPT API 호출
        response = client.chat.completions.create(model=model, messages=messages, response_format={'type': 'json_object'})

        try:
            result = response.choices[0].message.content
            return https_fn.Response(json.dumps(result), status=200, mimetype="application/json", headers=headers)
        except Exception as e:
            return https_fn.Response(
            json.dumps({"error": str(e), "note": f"{result}"}), status=404, mimetype="application/json", headers=headers
        )

    except Exception as e:
        return https_fn.Response(
            json.dumps({"error": str(e) + str(req.get_json())}), status=500, mimetype="application/json", headers=headers
        )


def contains_korean(text: str) -> bool:
    return bool(re.search(r'[\uac00-\ud7a3]', text))


def fetch_html(url: str) -> str:
    """지정된 URL에서 HTML을 가져옵니다."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
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


def extract_content_with_images(url: str) -> str:
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
    return "\n".join(sorted(extracted_content))