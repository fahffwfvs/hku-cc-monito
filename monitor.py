import requests
from bs4 import BeautifulSoup

TARGET_URL = "https://sweb.hku.hk/ccacad/ccc_appl/enrol_stat.html"
TARGET_COURSE = "CCST5037"

# 固化的 3 个 PushPlus Token
PUSHPLUS_TOKENS = [
    "89eb5d799743446694ef494b4a8c0613",
    "d38a29652e5441fb8b05c76118cae3b6",
    "3b7d564d6a3a40e3a9328b683537c89c"
]

def send_pushplus_multicast(title, content):
    """通过 PushPlus 给所有绑定的微信发送消息"""
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
                print(f"[+] 成员 {index} 微信推送成功！")
            else:
                print(f"[-] 成员 {index} 推送失败:", res.json().get("msg"))
        except Exception as e:
            print(f"[-] 成员 {index} 推送异常:", e)

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    print(f"[{TARGET_COURSE}] 开始检测空余名额...")
    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            err_msg = f"[-] 网页访问失败，HTTP 状态码: {response.status_code}"
            print(err_msg)
            send_pushplus_multicast(
                "❌ 监控脚本异常告警", 
                f"<b>【🚨 HKU 监控脚本异常】</b><br><br>无法访问 HKU 课程页面！<br>HTTP 状态码: {response.status_code}"
            )
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all('tr')
        
        found = False
        for row in rows:
            text = row.get_text()
            if TARGET_COURSE in text:
                found = True
                cols = [ele.text.strip() for ele in row.find_all(['td', 'th'])]
                
                # 准确提取各个字段
                course_code = cols[0] if len(cols) > 0 else TARGET_COURSE
                course_title = cols[1] if len(cols) > 1 else ""
                section = cols[2] if len(cols) > 2 else ""
                quota = cols[3] if len(cols) > 3 else "未明确"
                available_or_enrolled = cols[4] if len(cols) > 4 else "0"
                waitlist = cols[5] if len(cols) > 5 else "0"

                try:
                    available_seats = int(available_or_enrolled)
                except ValueError:
                    available_seats = 0

                print(f"当前 {TARGET_COURSE} 数据: {cols}")
                
                if available_seats > 0:
                    title = f"🚨 发现 {available_seats} 个空位！请立刻抢课！"
                else:
                    title = f"【课程状态巡检】{TARGET_COURSE} 剩余:{available_seats}"

                content = (
                    f"<b>【HKU {TARGET_COURSE} 课程巡检通知】</b><br><br>"
                    f"<b>课程代码:</b> {course_code}<br>"
                    f"<b>课程名称:</b> {course_title}<br>"
                    f"<b>班别 (Section):</b> {section}<br>"
                    f"<b>总名额 (Quota):</b> {quota}<br>"
                    f"<b>剩余名额 (Available):</b> <b style='color:{'red' if available_seats > 0 else 'black'}; font-size:20px;'>{available_seats}</b><br>"
                    f"<b>Waitlist (候补人数):</b> {waitlist}<br><br>"
                    f"<b>完整原始列:</b> {' | '.join(cols)}<br><br>"
                    f"{'<b>👉 请立刻登录 HKU SIS 系统抢课！</b>' if available_seats > 0 else '当前课程满员，系统持续监控中...'}"
                )
                
                send_pushplus_multicast(title, content)
                break
                
        if not found:
            err_msg = f"[-] 页面中未找到 {TARGET_COURSE} 课程数据。"
            print(err_msg)
            send_pushplus_multicast(
                "❌ 监控脚本数据异常", 
                f"<b>【🚨 HKU 监控脚本异常】</b><br><br>在页面中未找到课程 <b>{TARGET_COURSE}</b> 的表格数据。"
            )

    except Exception as e:
        err_msg = f"[-] 监控脚本运行发生严重错误: {e}"
        print(err_msg)
        send_pushplus_multicast(
            "❌ 监控脚本运行崩溃", 
            f"<b>【🚨 HKU 监控脚本崩溃】</b><br><br>运行发生严重异常：<br><code style='color:red;'>{e}</code>"
        )

if __name__ == "__main__":
    main()
