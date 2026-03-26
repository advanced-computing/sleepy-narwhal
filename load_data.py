import pandas as pd
import pandas_gbq
import requests

# 1. Project ID
PROJECT_ID = "sipa-adv-c-sleepy-narwhal"
# Name of Dataset
DATASET_ID = "nyc_data"


# ==========================================
# 2. load data
# ==========================================
def fetch_all_data(base_url):
    all_records = []
    limit = 2000
    offset = 0
    print(f"🌐start: {base_url}")
    while True:
        params = {"$limit": limit, "$offset": offset}
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            if not data:
                break
            all_records.extend(data)
            offset += limit
            print(f"  ... {len(all_records)} lines already")
        except Exception as e:
            print(f"❌ error occur: {e}")
            break
    return pd.DataFrame(all_records)


# ==========================================
# 3. Daily Inmates
# ==========================================
def process_inmates_data():
    print("\n📦 Dataset 1: Daily Inmates")
    url = "https://data.cityofnewyork.us/resource/7479-ugqb.json"

    df = fetch_all_data(url)
    if not df.empty:
        df.columns = df.columns.str.replace(r"[^a-zA-Z0-9_]", "_", regex=True)
        table_id = f"{DATASET_ID}.daily_inmates"
        print(f"🚀 {len(df)} update to BigQuery: {table_id}")

        pandas_gbq.to_gbq(
            df, table_id, project_id=PROJECT_ID, if_exists="replace", progress_bar=True
        )
        print("✅ Daily Inmates update successfully！")
    else:
        print("⚠️ No Inmates data。")


# ==========================================
# 4. Hate Crimes
# ==========================================
def process_hate_crimes_data():
    print("\n📦 Dataset 2: NYPD Hate Crimes")
    url = "https://data.cityofnewyork.us/resource/bqiq-cu78.json"
    df = fetch_all_data(url)
    if not df.empty:
        df.columns = df.columns.str.replace(r"[^a-zA-Z0-9_]", "_", regex=True)
        table_id = f"{DATASET_ID}.hate_crimes"
        print(f"🚀 {len(df)} update to BigQuery: {table_id}")

        pandas_gbq.to_gbq(
            df, table_id, project_id=PROJECT_ID, if_exists="replace", progress_bar=True
        )
        print("✅ Hate Crimes update successfully！")
    else:
        print("⚠️ No Hate Crimes data。")


# ==========================================
# 5. main
# ==========================================
if __name__ == "__main__":
    print(f"🔗 GCP Project ID: {PROJECT_ID}")
    process_inmates_data()
    process_hate_crimes_data()
    print("\n🎉 Look up at BigQuery！")
