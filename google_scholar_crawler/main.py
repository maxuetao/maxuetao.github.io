import os
import time
import random
import traceback
import json
from datetime import datetime
from scholarly import scholarly, ProxyGenerator
from fake_useragent import UserAgent
import signal
import sys

print("📘 程序已启动", flush=True)

# === 超时机制 ===
def handler(signum, frame):
    raise TimeoutError("⏰ 超时，Google Scholar 无响应。")

signal.signal(signal.SIGALRM, handler)
signal.alarm(120)  # 最长等待 2 分钟

# === 环境变量 ===
scholar_id = os.environ.get("GOOGLE_SCHOLAR_ID")
if not scholar_id:
    print("❌ 未设置环境变量 GOOGLE_SCHOLAR_ID")
    sys.exit(1)
print(f"🎯 目标 Scholar ID: {scholar_id}", flush=True)

# === 初始化代理和 UA ===
pg = ProxyGenerator()
pg.FreeProxies(repeat=1) # 使用免费代理池
scholarly.use_proxy(pg)

ua = UserAgent()
ua_list = [
    ua.random,
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)"
]

# === 重试逻辑 ===
author = None
for attempt in range(3):
    try:
        scholarly.set_user_agent(random.choice(ua_list))
        wait_time = random.uniform(5, 20)
        print(f"🕐 第 {attempt+1} 次尝试，等待 {wait_time:.1f} 秒...", flush=True)
        time.sleep(wait_time)

        author = scholarly.search_author_id(scholar_id)
        scholarly.fill(author, sections=['basics', 'indices', 'counts', 'publications'])
        print("✅ 抓取成功！", flush=True)
        break

    except Exception as e:
        print(f"⚠️ 第 {attempt+1} 次抓取失败: {e}")
        traceback.print_exc()
        time.sleep(15 + attempt * 10)

if not author:
    print("❌ 三次尝试均失败，退出。")
    sys.exit(1)

# === 数据处理与输出 ===
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
