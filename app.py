import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go

from deadline_db import (
    create_table,
    insert_deadlines,
    fetch_deadlines_between,
    extract_target_dates_from_csv,
    create_upload_log_table,
    insert_upload_log,
    fetch_latest_upload_log,
)


def main():
    st.set_page_config(layout="wide")
    st.title("日付別納期件数グラフ（平泉工場）")

    create_table()
    create_upload_log_table()

    latest_log = fetch_latest_upload_log()
    if latest_log:
        filename, upload_time = latest_log
        if isinstance(upload_time, str):
            try:
                upload_time = datetime.fromisoformat(upload_time)
            except Exception:
                pass
        st.markdown(
            f"📂 **最新アップロードファイル:** {filename}  （📅 {upload_time.strftime('%Y-%m-%d %H:%M:%S')}）"
        )
    else:
        st.markdown("まだCSVファイルがアップロードされていません。")

    uploaded_file = st.file_uploader("CSVファイルをアップロード", type="csv")

    if uploaded_file is not None:
        # 同名ファイルチェック
        from deadline_db import connect_db

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM upload_logs WHERE filename = ?", (uploaded_file.name,))
        count = cursor.fetchone()[0]
        conn.close()

        if count > 0:
            st.warning(f"ファイル名 '{uploaded_file.name}' は既にアップロードされています。上書きしますか？")
            if st.button("はい、上書きします"):
                process_upload(uploaded_file)
        else:
            process_upload(uploaded_file)

    draw_graph()


def process_upload(uploaded_file):
    try:
        records, date_series = extract_target_dates_from_csv(uploaded_file)
        insert_deadlines(records)
        insert_upload_log(uploaded_file.name)
        st.success(f"{len(records)} 件の納期データを登録しました。")
        # 更新されたアップロード情報の再表示
        latest_log = fetch_latest_upload_log()
        if latest_log:
            filename, upload_time = latest_log
            if isinstance(upload_time, str):
                try:
                    upload_time = datetime.fromisoformat(upload_time)
                except Exception:
                    pass
            st.markdown(
                f"📂 **最新アップロードファイル:** {filename}  （📅 {upload_time.strftime('%Y-%m-%d %H:%M:%S')}）"
            )
    except Exception as e:
        st.error(f"CSV処理中にエラーが発生しました: {e}")


def draw_graph():
    today = datetime.today().date()
    two_months_later = today + timedelta(days=60)
    start_str = today.strftime("%Y-%m-%d")
    end_str = two_months_later.strftime("%Y-%m-%d")

    results = fetch_deadlines_between(start_str, end_str)
    if not results:
        st.info("該当期間の納期データが存在しません。")
        return

    due_dates = [datetime.strptime(row[0], "%Y-%m-%d").date() for row in results]

    df_due = pd.DataFrame(due_dates, columns=["変換日付"])
    date_range = pd.date_range(start=today, end=two_months_later)
    count_df = pd.DataFrame({"日付": date_range.date, "件数": 0}).set_index("日付")

    count_series = df_due["変換日付"].value_counts().sort_index()
    for date, count in count_series.items():
        if date in count_df.index:
            count_df.loc[date, "件数"] = count

    def format_label(d):
        week_map = ["月", "火", "水", "木", "金", "土", "日"]
        return f"{d.month}/{d.day}<br>{week_map[d.weekday()]}"

    count_df["表示日付"] = [format_label(d) for d in count_df.index]

    fig = go.Figure(
        data=[
            go.Bar(
                x=count_df["表示日付"],
                y=count_df["件数"],
                marker_color="skyblue",
                text=count_df["件数"],
                textposition="outside",
            )
        ]
    )

    y_max = count_df["件数"].max()

    fig.update_layout(
        width=1200,
        height=600,
        margin=dict(l=20, r=20, t=60, b=80),
        xaxis_tickangle=0,
        xaxis_title="納期日",
        yaxis_title="件数",
        yaxis=dict(range=[0, y_max + (10 if y_max > 20 else 3)], tickangle=0),
        title="日付別納期件数（平泉工場）",
    )

    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
