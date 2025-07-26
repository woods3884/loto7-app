import streamlit as st
import pandas as pd
import random
from collections import Counter
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- 設定 ---
DATA_DIR = "data"
DATA_PATH = os.path.join(DATA_DIR, "LOTO7_ALL.csv")

# --- 初期フォルダ作成 ---
os.makedirs(DATA_DIR, exist_ok=True)

# --- データ読み込み ---
def load_data():
    if not os.path.exists(DATA_PATH):
        columns = ["抽選日", "数字１", "数字２", "数字３", "数字４", "数字５", "数字６", "数字７", "数字B1", "数字B2"]
        return pd.DataFrame(columns=columns)
    
    df = pd.read_csv(DATA_PATH, encoding="utf-8")
    
    # 列名の標準化
    df.rename(columns={
        "抽選日": "date",
        "数字１": "num1",
        "数字２": "num2",
        "数字３": "num3",
        "数字４": "num4",
        "数字５": "num5",
        "数字６": "num6",
        "数字７": "num7",
        "数字B1": "bonus1",
        "数字B2": "bonus2"
    }, inplace=True)
    return df

# --- 最新データ取得（楽天） ---
def fetch_latest_loto7():
    url = "https://takarakuji.rakuten.co.jp/loto7/"
    try:
        res = requests.get(url, timeout=10)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")

        # 抽選日
        date_tag = soup.find("th", string="抽せん日")
        if date_tag is None:
            return None, "抽選日が見つかりません"
        date_str = date_tag.find_next("td").text.strip()
        draw_date = datetime.strptime(date_str, "%Y年%m月%d日").strftime("%Y-%m-%d")

        # 数字
        num_tags = soup.select(".number--loto7 .number__box")
        numbers = [int(tag.text.strip()) for tag in num_tags if tag.text.strip().isdigit()]
        if len(numbers) < 9:
            return None, "数字が不足しています"

        return {
            "抽選日": draw_date,
            "数字１": numbers[0],
            "数字２": numbers[1],
            "数字３": numbers[2],
            "数字４": numbers[3],
            "数字５": numbers[4],
            "数字６": numbers[5],
            "数字７": numbers[6],
            "数字B1": numbers[7],
            "数字B2": numbers[8]
        }, None
    except Exception as e:
        return None, f"取得エラー: {e}"

# --- 頻出数字ランキング ---
def get_top_numbers(df, top_n=10):
    all_numbers = df[["num1", "num2", "num3", "num4", "num5", "num6", "num7"]].values.flatten()
    counter = Counter(all_numbers)
    return counter.most_common(top_n)

# --- おすすめ数字（ランダム7個）×5口 ---
def generate_lucky_numbers(kuchi=5):
    return [sorted(random.sample(range(1, 38), 7)) for _ in range(kuchi)]

# --- Streamlit UI ---
st.set_page_config(page_title="ロト7アプリ", layout="centered")
st.title("🎯 ロト7 出現数字分析＆予測アプリ")

# --- データ読込 ---
df = load_data()

# --- 最新データ取得ボタン ---
st.subheader("📥 最新の当選結果を取得してCSVに追加")
if st.button("🧾 最新結果を取得"):
    new_data, error = fetch_latest_loto7()
    if error:
        st.error(f"❌ {error}")
    elif new_data["抽選日"] in df["date"].values:
        st.warning("⚠️ すでに登録済みのデータです")
    else:
        df = pd.concat([pd.DataFrame([new_data]), df], ignore_index=True)
        df.to_csv(DATA_PATH, index=False, encoding="utf-8-sig")
        st.success(f"✅ {new_data['抽選日']} の結果を追加しました！")

# --- 頻出ランキング表示 ---
st.subheader("📊 過去の頻出数字（TOP10）")
top_nums = get_top_numbers(df)
for num, count in top_nums:
    st.markdown(f"- **{num}：{count} 回**")

# --- おすすめ数字（5口） ---
st.subheader("🔮 おすすめ数字（ランダム生成・7個 × 5口）")
if st.button("🔁 もう一度生成"):
    st.session_state["lucky"] = generate_lucky_numbers()
if "lucky" not in st.session_state:
    st.session_state["lucky"] = generate_lucky_numbers()

for i, nums in enumerate(st.session_state["lucky"], 1):
    st.write(f"{i}口目：🎯 {'・'.join(str(n) for n in nums)}")

# --- 登録済データ表示 ---
st.subheader("📅 登録済みデータ")
st.dataframe(df)
