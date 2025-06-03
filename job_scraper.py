import requests
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import re
from datetime import datetime
import time

# 區域代碼對照
area_codes = {
    "台北市": "6001001000",
    "新竹市": "6001006000",
    "台中市": "6001002000",
    "台南市": "6001005000",
    "高雄市": "6001004000"
}

# 目標關鍵字
keywords = ["行銷", "人資"]

# 薪資轉換函數
def parse_salary(salary_str):
    if not salary_str or "月薪" not in salary_str:
        return None

    match = re.findall(r"(\d+(?:,\d+)?)(?:~(\d+(?:,\d+)?))?", salary_str.replace(",", ""))
    if match:
        nums = match[0]
        nums = [int(n) for n in nums if n]
        if len(nums) == 2:
            avg_salary = sum(nums) / 2
        elif len(nums) == 1:
            avg_salary = nums[0]
        else:
            return None
        return round(avg_salary / 10000, 1)
    return None

# 抓取職缺資料
def fetch_jobs(keyword, area_code, pages=3):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.104.com.tw/jobs/search/"
    }
    all_jobs = []

    for page in range(1, pages + 1):
        print(f"🔍 抓取 {keyword}（{area_code}）第 {page} 頁...")
        params = {
            "ro": "0",
            "kwop": "7",
            "keyword": keyword,
            "area": area_code,
            "order": "11",
            "asc": "0",
            "page": str(page),
            "mode": "s",
            "jobsource": "2018indexpoc"
        }
        try:
            res = requests.get("https://www.104.com.tw/jobs/search/list", headers=headers, params=params)
            res.raise_for_status()
            jobs = res.json().get("data", {}).get("list", [])
            for job in jobs:
                salary = job.get("salaryDesc")
                salary_value = parse_salary(salary)
                if salary_value is not None:
                    all_jobs.append({
                        "職缺": keyword,
                        "地區": job.get("jobAddrNoDesc"),
                        "城市": area_code,
                        "公司": job.get("custName"),
                        "薪資描述": salary,
                        "薪資萬元": salary_value
                    })
            time.sleep(1)
        except Exception as e:
            print(f"❌ 錯誤：{e}")
    return all_jobs

# 主程式
if __name__ == "__main__":
    results = []

    for city, area_code in area_codes.items():
        for keyword in keywords:
            jobs = fetch_jobs(keyword, area_code)
            for job in jobs:
                job["城市"] = city
            results.extend(jobs)

    df = pd.DataFrame(results)

    # 儲存 Excel
    df["薪資萬元"] = df["薪資萬元"].apply(lambda x: f"{x} 萬元")
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_file = f"104薪資比較_{now}.xlsx"
    df.to_excel(excel_file, index=False)
    print(f"✅ 資料儲存完成：{excel_file}")

    # 平均薪資圖表
    df["薪資數值"] = df["薪資萬元"].str.replace(" 萬元", "").astype(float)
    avg_salary_df = df.groupby(["城市", "職缺"])["薪資數值"].mean().reset_index()

    plt.figure(figsize=(10, 6))
    sns.set(style="whitegrid", font="Microsoft JhengHei", palette="Set2")

    ax = sns.barplot(data=avg_salary_df, x="城市", y="薪資數值", hue="職缺")

    for container in ax.containers:
        ax.bar_label(container, fmt="%.1f", label_type="edge", padding=3)

    plt.title("不同城市與職缺的平均薪資比較", fontsize=14)
    plt.xlabel("城市")
    plt.ylabel("平均薪資（萬元／月）")

    # ✅ 圖例移到圖表外側
    plt.legend(title="職缺", loc="center left", bbox_to_anchor=(1.02, 0.5))
    plt.tight_layout(rect=[0, 0, 0.85, 1])  # 調整畫布以容納圖例
    plt.show()

