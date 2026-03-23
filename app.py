import pandas as pd
import re
import zipfile
import os
import streamlit as st
import tempfile

# -------- PAGE CONFIG --------
st.set_page_config(page_title="WhatsApp Analyzer", layout="wide")

# -------- CLEAR CACHE --------
st.cache_data.clear()

# -------- RESET BUTTON --------
if st.button("🔄 Reset App"):
    st.cache_data.clear()
    st.rerun()

# -------- TITLE --------
st.markdown("<h1 style='text-align:center;'>📊 WhatsApp Chat Analyzer 🚀</h1>", unsafe_allow_html=True)

# -------- FILE UPLOAD --------
uploaded_file = st.file_uploader("📂 Upload WhatsApp Chat (.txt or .zip)", type=["txt", "zip"])

if uploaded_file:

    # -------- SAVE TEMP FILE --------
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getbuffer())
        file_path = tmp_file.name

    # -------- HANDLE ZIP --------
    if uploaded_file.name.endswith(".zip"):
        st.info("📦 Extracting ZIP file...")

        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            txt_files = [f for f in os.listdir(temp_dir) if f.endswith(".txt")]

            if not txt_files:
                st.error("❌ No .txt file found inside ZIP")
                st.stop()

            file_path = os.path.join(temp_dir, txt_files[0])
            st.success(f"✅ Using file: {txt_files[0]}")

            with open(file_path, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
    else:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

    # -------- PARSER --------
    data = []

    for line in lines:
        match = re.match(r"(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{1,2}(?:\s?[APMapm]{2})?) - (.*?): (.*)", line)

        if not match:
            match = re.match(r"\[(.*?)\] (.*?): (.*)", line)

        if match:
            parts = match.groups()

            if len(parts) == 4:
                date, time, user, msg = parts
            else:
                datetime_part, user, msg = parts
                try:
                    date, time = datetime_part.split(", ")
                except:
                    continue

            data.append([date, time, user, msg])

    df = pd.DataFrame(data, columns=["Date", "Time", "User", "Message"])

    if df.empty:
        st.error("❌ Could not parse chat.")
        st.stop()

    # -------- CLEAN --------
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    df["Hour"] = pd.to_datetime(df["Time"], errors="coerce").dt.hour
    df["Emoji_Count"] = df["Message"].apply(lambda x: len(re.findall(r"[^\w\s,]", x)))

    # -------- STATS --------
    daily = df.groupby("Date").size()
    hourly = df.groupby("Hour").size()
    user_total = df["User"].value_counts()
    emoji_user = df.groupby("User")["Emoji_Count"].sum()

    total_msgs = len(df)
    avg_per_day = total_msgs // len(daily) if len(daily) > 0 else 0

    # -------- METRICS --------
    col1, col2 = st.columns(2)
    col1.metric("📩 Total Messages", total_msgs)
    col2.metric("📅 Avg / Day", avg_per_day)

    st.divider()

    # -------- USERS --------
    st.markdown("## 👤 Users")
    user_df = user_total.reset_index()
    user_df.columns = ["User", "Messages"]
    st.dataframe(user_df, use_container_width=True)

    # -------- EMOJIS --------
    st.markdown("## 😂 Emoji Usage")
    emoji_df = emoji_user.reset_index()
    emoji_df.columns = ["User", "Emojis"]
    st.dataframe(emoji_df, use_container_width=True)

    # -------- DAILY --------
    st.markdown("## 📅 Daily Message Counts")

    daily_df = daily.reset_index()
    daily_df.columns = ["Date", "Messages"]
    daily_df["Date"] = daily_df["Date"].dt.strftime("%Y-%m-%d")

    st.dataframe(daily_df, use_container_width=True)

    # -------- PEAK --------
    peak_day = daily.idxmax()
    peak_val = daily.max()
    st.success(f"🔥 Peak Day: {peak_day.date()} ({peak_val} messages)")

    # -------- TOP DAYS --------
    st.markdown("## 🏆 Top 3 Active Days")
    top_days = daily.sort_values(ascending=False).head(3)

    for date, count in top_days.items():
        st.write(f"{date.date()} : {count}")

    st.divider()

    # -------- GRAPHS --------
    st.markdown("## 📈 Graphical Analysis")

    st.markdown("### 📅 Daily Message Trend")
    st.caption("Shows how chat activity changes over time.")
    st.line_chart(daily)

    st.markdown("### 👤 Messages per User")
    st.caption("Total messages sent by each user.")
    st.bar_chart(user_total)

    st.markdown("### ⏰ Activity by Hour")
    st.caption("Most active hours of the day.")
    st.bar_chart(hourly)

    st.markdown("### 😂 Emoji Usage")
    st.caption("Emoji usage comparison.")
    st.bar_chart(emoji_user)

    st.divider()

    # -------- SUMMARY --------
    st.markdown("## 🧠 Smart Summary")

    summary = []
    low_day = daily.idxmin()

    summary.append(f"Peak activity on {peak_day.date()} with {peak_val} messages.")
    summary.append(f"Lowest activity on {low_day.date()}.")

    if len(user_total) >= 2:
        diff = abs(user_total.iloc[0] - user_total.iloc[1])
        if diff < total_msgs * 0.1:
            summary.append("Users contributed almost equally.")
        else:
            summary.append(f"{user_total.idxmax()} dominated the conversation.")

    summary.append(f"{emoji_user.idxmax()} used more emojis.")

    if peak_val > avg_per_day * 2:
        summary.append("Chat shows spike-based activity.")
    else:
        summary.append("Chat is consistent.")

    summary.append(f"Total {total_msgs} messages with avg {avg_per_day}/day.")

    for s in summary:
        st.write(f"• {s}")
