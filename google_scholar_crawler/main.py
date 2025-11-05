import os
import time
import random
import traceback
import json
from datetime import datetime
from scholarly import scholarly
from fake_useragent import UserAgent
import signal
import sys

print("📘 程序已启动", flush=True)

# === 超时机制（Linux 层） ===
def handler(signum, frame):
    raise TimeoutError("⏰ 程序运行超时，可能被 Google Scholar 拦截。")

signal.signal(signal.SIGALRM, handler)
signal.alarm(180)  # 整个脚本最长 3 分钟

# === 环境变量 ===
scholar_id = os.environ.get("GOOGLE_SCHOLAR_ID")
if not scholar_id:
    print("❌ 未设置环境变量 GOOGLE_SCHOLAR_ID")
    sys.exit(1)
print(f"🎯 目标 Scholar ID: {scholar_id}", flush=True)

# === 随机 UA ===
ua = UserAgent()
ua_list = [
    ua.random,
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)"
]
os.environ["USER_AGENT"] = random.choice(ua_list)

# === 抓取逻辑 ===
author = None
for attempt in range(3):
    try:
        wait_time = random.uniform(5, 20)
        print(f"🕐 第 {attempt+1} 次尝试，等待 {wait_time:.1f} 秒...", flush=True)
        time.sleep(wait_time)

        # 手动控制超时，防止 scholarly 卡死
        start = time.time()
        author = scholarly.search_author_id(scholar_id)
        scholarly.fill(author, sections=['basics', 'indices', 'counts', 'publications'])
        elapsed = time.time() - start
        print(f"✅ 抓取成功，用时 {elapsed:.1f} 秒", flush=True)
        break

    except Exception as e:
        print(f"⚠️ 第 {attempt+1} 次失败: {e}")
        traceback.print_exc()
        time.sleep(15 + attempt * 10)

if not author:
    print("❌ 三次尝试后仍未成功，跳过本次运行。")
    sys.exit(0)  # 注意退出 0（不算错误）

# === 输出结果 ===
author['updated'] = str(datetime.now())
author['publications'] = {v['author_pub_id']: v for v in author['publications']}

os.makedirs('results', exist_ok=True)

with open('results/gs_data.json', 'w') as f:
    json.dump(author, f, ensure_ascii=False, indent=2)
print("💾 已保存结果到 results/gs_data.json")

shieldio_data = {
    "schemaVersion": 1,
    "label": "citations",
    "message": f"{author.get('citedby', 'N/A')}",
}
with open('results/gs_data_shieldsio.json', 'w') as f:
    json.dump(shieldio_data, f, ensure_ascii=False, indent=2)
print("✅ 已生成 Shields.io JSON 文件")

signal.alarm(0)
print("🎉 程序运行完成", flush=True)
