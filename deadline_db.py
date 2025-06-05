import os
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE = "deadlines"
SUPABASE_LOG_TABLE = "upload_logs"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def insert_deadlines(records):
    cleaned_records = []
    for record in records:
        # NaNやinfをNoneに変換1
        cleaned = {
            "due_date": record["due_date"],
        }
        cleaned_records.append(cleaned)

    supabase.table(SUPABASE_TABLE).insert(cleaned_records).execute()


def fetch_deadlines_between(start_date, end_date):
    result = (
        supabase.table(SUPABASE_TABLE)
        .select("*")
        .gte("due_date", start_date)
        .lte("due_date", end_date)
        .execute()
    )
    return [(row["due_date"],) for row in result.data]


def create_table():
    pass  # Supabaseでは不要


def create_upload_log_table():
    pass  # Supabaseでは不要


def insert_upload_log(filename):
    supabase.table(SUPABASE_LOG_TABLE).insert(
        {"filename": filename, "upload_time": datetime.now().isoformat()}
    ).execute()


def fetch_latest_upload_log():
    result = supabase.table(SUPABASE_LOG_TABLE).select("*").order("upload_time", desc=True).limit(1).execute()
    if result.data:
        return result.data[0]["filename"], result.data[0]["upload_time"]
    return None


def extract_target_dates_from_csv(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file, encoding="cp932")
    except UnicodeDecodeError:
        df = pd.read_csv(uploaded_file, encoding="utf-8")

    target_column = "00041確認納期（回答納期）01"

    if target_column not in df.columns:
        raise Exception(f"CSVに '{target_column}' 列が見つかりません")

    # 日付変換：YYMMDD形式 → YYYY-MM-DD
    def convert_ymd(value):
        try:
            value_str = str(value).strip()
            return datetime.strptime(value_str, "%y%m%d").strftime("%Y-%m-%d")
        except Exception:
            return None

    df["converted_date"] = df[target_column].apply(convert_ymd)
    df_cleaned = df[df["converted_date"].notna()].copy()

    records = [{"due_date": date} for date in df_cleaned["converted_date"]]

    return records, df_cleaned["converted_date"]
