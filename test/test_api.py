import requests, json

if __name__ == "__main__":
    URL = "http://127.0.0.1:5001/chung-mo/us-central1/parse_voucher_handler"
    data = {"link": "https://mcard.cryucard.com/c/JjJ9DKvEsmYtOHk5VkZl"}

    res = requests.post(URL, json=data)
    data = res.json()
    jdata = json.loads(data)
    print(res.status_code)
    print(jdata)