import pandas as pd
import sqlite3
from datetime import datetime

DB_PATH = "deadline_data.db"


def connect_db():
    return sqlite3.connect(DB_PATH)


def create_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS deadlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            due_date DATE
        )
        """
    )
    conn.commit()
    conn.close()


def insert_deadlines(records):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO deadlines (due_date) VALUES (?)", records)
    conn.commit()
    conn.close()


def fetch_deadlines_between(start_date, end_date):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT due_date FROM deadlines
        WHERE due_date BETWEEN ? AND ?
        ORDER BY due_date
        """,
        (start_date, end_date),
    )
    results = cursor.fetchall()
    conn.close()
    return results


def extract_target_dates_from_csv(csv_file_or_path, keyword="00041"):
    # csv_file_or_path はパス or BytesIO どちらも対応
    df = pd.read_csv(csv_file_or_path, encoding="cp932")
    target_cols = [col for col in df.columns if keyword in col]
    if not target_cols:
        raise ValueError("納期日カラムが見つかりませんでした")
    target_col = target_cols[0]

    df["変換日付"] = pd.to_datetime(df[target_col].astype(str), format="%y%m%d", errors="coerce")
    df = df.dropna(subset=["変換日付"])
    records = [(d.strftime("%Y-%m-%d"),) for d in df["変換日付"]]
    return records, df["変換日付"]


# アップロード履歴テーブル関連

def create_upload_log_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS upload_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            upload_time DATETIME
        )
        """
    )
    conn.commit()
    conn.close()


def insert_upload_log(filename):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO upload_logs (filename, upload_time) VALUES (?, ?)",
        (filename, datetime.now())
    )
    conn.commit()
    conn.close()


def fetch_latest_upload_log():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT filename, upload_time FROM upload_logs ORDER BY upload_time DESC LIMIT 1"
    )
    result = cursor.fetchone()
    conn.close()
    return result  # (filename, upload_time) or None
