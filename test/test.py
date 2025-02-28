import requests, json


def get_voucher_api(API_URL: str, link: str) -> None:
    res = requests.post(API_URL, json={"link": link})
    data = res.json()
    jdata = json.loads(data)
    print(res.status_code)
    print(jdata)
    print(type(jdata))

if __name__ == "__main__":
    # API_URL = "http://127.0.0.1:5001/chung-mo/us-central1/parse_voucher_handler"
    API_URL = "http://127.0.0.1:5001/chung-mo/us-central1/test_handler"
    link = "https://mcard.cryucard.com/c/JjJ9DKvEsmYtOHk5VkZl"
    get_voucher_api(API_URL, link)