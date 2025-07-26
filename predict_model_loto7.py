import pandas as pd
import joblib
import os
import random

CSV_PATH = "LOTO7_ALL.csv"
MODEL_DIR = "models_loto7"

def create_features(df):
    nums = df[["num1", "num2", "num3", "num4", "num5", "num6", "num7"]]
    freq = pd.Series(nums.values.flatten()).value_counts().sort_index()
    freq = freq.reindex(range(1, 38), fill_value=0)
    return freq.to_frame(name="count").reset_index().rename(columns={"index": "number"})

def load_models():
    models = {}
    for n in range(1, 38):
        path = os.path.join(MODEL_DIR, f"model_{n}.pkl")
        models[n] = joblib.load(path)
    return models

def predict_numbers(df, models):
    past_df = df.tail(20)  # 最新20回から特徴量を作成
    features = create_features(past_df)["count"].tolist()
    X = [features]

    probs = {}
    for n, model in models.items():
        prob = model.predict_proba(X)[0][1]  # [0]=negative, [1]=positive
        probs[n] = prob

    # 確率の高い順に並べて、7個ランダム抽出（やや変化をもたせる）
    top = sorted(probs.items(), key=lambda x: x[1], reverse=True)
    candidates = [n for n, p in top[:20]]  # 上位20からランダムに7つ
    return sorted(random.sample(candidates, 7))

def generate_recommendations(n_sets=5):
    df = pd.read_csv(CSV_PATH)
    df.rename(columns={
        "数字１": "num1", "数字２": "num2", "数字３": "num3",
        "数字４": "num4", "数字５": "num5", "数字６": "num6", "数字７": "num7"
    }, inplace=True)

    models = load_models()
    all_sets = []
    for _ in range(n_sets):
        pred = predict_numbers(df, models)
        all_sets.append(pred)
    return all_sets

if __name__ == "__main__":
    results = generate_recommendations()
    print("🎰 AI予測によるおすすめ数字（5口）")
    for i, nums in enumerate(results, 1):
        print(f"{i}口目：", "・".join(map(str, nums)))
