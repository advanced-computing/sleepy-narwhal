import os

import pandas as pd
import pandas_gbq
import requests

# ==========================================
# 1. Configuration
# ==========================================
PROJECT_ID = "sipa-adv-c-sleepy-narwhal"
DATASET_ID = "credit_risk_data"
# Fred API
FRED_API_KEY = "449c21ccb425167e72778c12cf10b63f"


# ==========================================
# 2. Fetch data from FRED
# ==========================================
def fetch_fred_series(series_id):
    """
    从 FRED 获取指定的时间序列数据。
    """
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {"series_id": series_id, "api_key": FRED_API_KEY, "file_type": "json"}

    print(f"🌐 Start fetching {series_id} from FRED...")
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # FRED 的实际数据存在 'observations' 列表里
        observations = data.get("observations", [])
        if not observations:
            return pd.DataFrame()

        df = pd.DataFrame(observations)

        # 只需要 date 和 value 两列
        df = df[["date", "value"]]

        # FRED 会把节假日缺失的数据标记为 '.'，我们需要过滤掉它们
        df = df[df["value"] != "."]

        # 转换数据类型
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = df["value"].astype(float)

        print(f"  ... {len(df)} records fetched and cleaned.")
        return df

    except Exception as e:
        print(f"❌ Error occurred while fetching {series_id}: {e}")
        return pd.DataFrame()


# ==========================================
# 3. Process & Upload: Investment Grade (IG) Spread
# ==========================================
def process_ig_spread():
    print("\n📦 Dataset 1: ICE BofA US Corporate (IG) OAS")
    # BAMLC0A0CM 是投资级信用利差的代码
    df = fetch_fred_series("BAMLC0A0CM")

    if not df.empty:
        # 重命名列名以符合数据库规范
        df.rename(columns={"value": "spread"}, inplace=True)
        table_id = f"{DATASET_ID}.ig_spread"

        print(f"🚀 Pushing {len(df)} rows to BigQuery: {table_id}")
        pandas_gbq.to_gbq(
            df, table_id, project_id=PROJECT_ID, if_exists="replace", progress_bar=True
        )
        print("✅ IG Spread updated successfully！")
    else:
        print("⚠️ No IG Spread data retrieved.")


# ==========================================
# 4. Process & Upload: High Yield (HY) Spread
# ==========================================
def process_hy_spread():
    print("\n📦 Dataset 2: ICE BofA US High Yield OAS")
    # BAMLH0A0HYM2 是高收益级（垃圾债）信用利差的代码
    df = fetch_fred_series("BAMLH0A0HYM2")

    if not df.empty:
        # 重命名列名以符合数据库规范
        df.rename(columns={"value": "spread"}, inplace=True)
        table_id = f"{DATASET_ID}.hy_spread"

        print(f"🚀 Pushing {len(df)} rows to BigQuery: {table_id}")
        pandas_gbq.to_gbq(
            df, table_id, project_id=PROJECT_ID, if_exists="replace", progress_bar=True
        )
        print("✅ High Yield Spread updated successfully！")
    else:
        print("⚠️ No High Yield Spread data retrieved.")


# ==========================================
# 5. Main Execution
# ==========================================
if __name__ == "__main__":
    print(f"🔗 GCP Project ID: {PROJECT_ID}")

    process_ig_spread()
    process_hy_spread()

    print("\n🎉 All FRED Data loaded! Look up at BigQuery！")
