import requests
from bs4 import BeautifulSoup

TARGET_URL = "https://sweb.hku.hk/ccacad/ccc_appl/enrol_stat.html"
TARGET_COURSE = "CCST5037"

# 已填入你的 2 个用户 Token
PUSHPLUS_TOKENS = [
    "89eb5d799743446694ef494b4a8c0613",
    "d38a29652e5441fb8b05c76118cae3b6"
]

def send_pushplus_multicast(title, content):
    """通过 PushPlus 给所有绑定的微信发送抢课提醒"""
    url = "http://www.pushplus.plus/send"
    for index, token in enumerate(PUSHPLUS_TOKENS, 1):
        payload = {
            "token": token.strip(),
            "title": title,
            "content": content,
            "template": "html"
        }
        try:
            res = requests.post(url, json=payload, timeout=10)
            if res.json().get("code") == 200:
                print(f"[+] 成员 {index} 微信抢课提醒推送成功！")
            else:
                print(f"[-] 成员 {index} 推送失败:", res.json().get("msg"))
        except Exception as e:
            print(f"[-] 成员 {index} 推送发生异常:", e)

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    print(f"[{TARGET_COURSE}] 开始检测空余名额...")
    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            print(f"[-] 网页访问失败，HTTP 状态码: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all('tr')
        
        found = False
        for row in rows:
            text = row.get_text()
            if TARGET_COURSE in text:
                found = True
                cols = [ele.text.strip() for ele in row.find_all(['td', 'th'])]
                
                try:
                    available_seats = int(cols[-2])
                except ValueError:
                    available_seats = 0

                print(f"当前 {TARGET_COURSE} 状态数据: {' | '.join(cols)}")
                
                # 判断逻辑：剩余名额不为 0 即代表有空位
                if available_seats > 0:
                    print(f"🎉 发现空位！剩余名额: {available_seats} 个，准备触发微信抢课提醒...")
                    title = f"🚨 CCST5037 抢课提醒！当前有 {available_seats} 个空位！"
                    content = (
                        f"<b>【速去 SIS 抢课】</b><br><br>"
                        f"课程代码: {TARGET_COURSE}<br>"
                        f"剩余名额: <b style='color:red;'>{available_seats}</b><br>"
                        f"完整信息: {' | '.join(cols)}<br><br>"
                        f"<b>请立刻登录 HKU SIS 系统！</b>"
                    )
                    send_pushplus_multicast(title, content)
                else:
                    print("⚠️ 当前课程还是满的，暂不触发微信推送。")
                break
                
        if not found:
            print(f"[-] 页面中未找到 {TARGET_COURSE} 课程数据。")

    except Exception as e:
        print(f"[-] 监控脚本运行发生错误: {e}")

if __name__ == "__main__":
    main()
