import requests
from bs4 import BeautifulSoup

TARGET_URL = "https://sweb.hku.hk/ccacad/ccc_appl/enrol_stat.html"
TARGET_COURSE = "CCST5037"

# 固化的 3 个 PushPlus Token（已添加你的新朋友）
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
            "title": title,  # 微信卡片中的设备名称/标题
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
        
        # 异常捕获 1：网页状态码非 200 时发微信告警
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
                
                # 提取剩余名额
                try:
                    available_seats = int(cols[-2])
                except ValueError:
                    available_seats = 0

                print(f"当前 {TARGET_COURSE} 状态数据: {' | '.join(cols)}")
                
                # 根据名额设置动态标题（设备名称栏）
                if available_seats > 0:
                    title = f"🚨 发现 {available_seats} 个空位！请立刻抢课！"
                else:
                    title = f"【课程状态巡检】课程代码: {TARGET_COURSE}"

                content = (
                    f"<b>【HKU {TARGET_COURSE} 课程巡检通知】</b><br><br>"
                    f"课程代码: {TARGET_COURSE}<br>"
                    f"剩余名额: <b style='color:{'red' if available_seats > 0 else 'black'}; font-size:18px;'>{available_seats}</b><br>"
                    f"完整信息: {' | '.join(cols)}<br><br>"
                    f"{'<b>👉 请立刻登录 HKU SIS 系统抢课！</b>' if available_seats > 0 else '当前课程满员，系统持续监控中...'}"
                )
                
                # 无论是否为 0，均进行播报
                send_pushplus_multicast(title, content)
                break
                
        # 异常捕获 2：找不到课程数据时发微信告警
        if not found:
            err_msg = f"[-] 页面中未找到 {TARGET_COURSE} 课程数据。"
            print(err_msg)
            send_pushplus_multicast(
                "❌ 监控脚本数据异常", 
                f"<b>【🚨 HKU 监控脚本异常】</b><br><br>在页面中未找到课程 <b>{TARGET_COURSE}</b> 的表格数据，请检查网页结构是否变更。"
            )

    # 异常捕获 3：程序崩溃/网络超时发微信告警
    except Exception as e:
        err_msg = f"[-] 监控脚本运行发生严重错误: {e}"
        print(err_msg)
        send_pushplus_multicast(
            "❌ 监控脚本运行崩溃", 
            f"<b>【🚨 HKU 监控脚本崩溃】</b><br><br>运行发生严重异常：<br><code style='color:red;'>{e}</code>"
        )

if __name__ == "__main__":
    main()
