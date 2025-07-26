import streamlit as st
import pandas as pd
import numpy as np
import random
import os
import datetime
from lightgbm import LGBMClassifier
import joblib
from bs4 import BeautifulSoup
import requests

# --- 定数 ---
CSV_PATH = "LOTO7_ALL.csv"
MODEL_PATH = "loto7_model.pkl"

# --- 🔮 ランダムおすすめ数字（先頭に表示） ---
st.header("\U0001F52E おすすめ数字（ランダム生成・7個\u00d75口）")

def generate_lucky_numbers():
    return [sorted(random.sample(range(1, 38), 7)) for _ in range(5)]

if 'lucky_numbers' not in st.session_state:
    st.session_state.lucky_numbers = generate_lucky_numbers()

if st.button("\U0001F4C4 もう一度生成"):
    st.session_state.lucky_numbers = generate_lucky_numbers()

for i, numbers in enumerate(st.session_state.lucky_numbers, 1):
    st.write(f"{i}口目：\U0001f3af {'・'.join(str(n) for n in numbers)}")

# --- 📥 最新当選結果の自動取得（楽天サイト対応） ---
st.title("\U0001F4E5 最新当選データを自動取得してCSVに追加")

if st.button("\U0001F4C4 最新結果を取得して反映"):
    try:
        url = "https://www.rakuten-lottery.jp/takarakuji/loto7/"
        res = requests.get(url)
        soup = BeautifulSoup(res.content, "html.parser")

        draw_area = soup.find("div", class_="contentsBox result")
        draw_date = soup.find("span", class_="lotDate").text.strip()
        numbers = draw_area.find_all("li", class_="lotnum")
        nums = [int(n.text.strip()) for n in numbers[:7]]
        bonus = [int(n.text.strip()) for n in numbers[7:9]]

        new_row = {
            "抽選日": draw_date,
            "num1": nums[0], "num2": nums[1], "num3": nums[2],
            "num4": nums[3], "num5": nums[4], "num6": nums[5], "num7": nums[6],
            "bonus1": bonus[0], "bonus2": bonus[1]
        }

        df = pd.DataFrame([new_row])

        if os.path.exists(CSV_PATH):
            old = pd.read_csv(CSV_PATH)
            if draw_date not in old["抽選日"].values:
                pd.concat([old, df], ignore_index=True).to_csv(CSV_PATH, index=False)
                st.success("新しい当選データを追加しました")
            else:
                st.info("最新データは既に登録済みです")
        else:
            df.to_csv(CSV_PATH, index=False)
            st.success("初回データを保存しました")

    except Exception as e:
        st.error(f"\u2716 データ取得に失敗しました：{e}")

# --- 🤖 AI予測 ---
st.title("\U0001F916 AI予測に基づくおすすめ数字（5口）")

def create_features(df):
    nums = df[["num1", "num2", "num3", "num4", "num5", "num6", "num7"]]
    flat = nums.values.flatten()
    counts = pd.Series(flat).value_counts().sort_index()
    all_numbers = pd.Series(range(1, 38))
    full_counts = all_numbers.map(counts).fillna(0)
    return pd.DataFrame({"number": all_numbers, "count": full_counts})

if os.path.exists(CSV_PATH) and os.path.exists(MODEL_PATH):
    try:
        data = pd.read_csv(CSV_PATH)
        features = create_features(data)["count"].values.reshape(-1, 1)
        model = joblib.load(MODEL_PATH)
        probas = model.predict_proba(features)[:, 1]

        ai_top = pd.Series(probas, index=range(1, 38)).sort_values(ascending=False).head(20).index.tolist()

        st.subheader("\U0001F4A1 AI予測おすすめ数字：")
        for i in range(5):
            st.write(f"{i+1}口目：\U0001f3af {'・'.join(str(n) for n in sorted(random.sample(ai_top, 7)))}")

    except Exception as e:
        st.error(f"AI予測に失敗しました：{e}")
else:
    st.warning("CSVファイルまたはモデルファイルが見つかりません。")
