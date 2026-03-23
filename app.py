import pandas as pd
import re
import zipfile
import os
import streamlit as st

st.set_page_config(page_title="WhatsApp Analyzer", layout="wide")
st.title("📊 WhatsApp Chat Analyzer")

# -------- FILE UPLOAD --------
uploaded_file = st.file_uploader("Upload WhatsApp Chat (.txt or .zip)", type=["txt", "zip"])

if uploaded_file:

    file_path = uploaded_file.name

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # -------- HANDLE ZIP --------
    if file_path.endswith(".zip"):
        st.write("📦 Extracting ZIP file...")
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall()

        for f in os.listdir():
            if f.endswith(".txt"):
                file_path = f
                st.success(f"✅ Found chat file: {file_path}")
                break

    # -------- READ FILE --------
    with open(file_path, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    data = []

    # -------- UNIVERSAL PARSER --------
    for line in lines:

        # Android format
        match = re.match(r"(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{1,2}(?:\s?[APMapm]{2})?) - (.*?): (.*)", line)

        # iPhone format
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

    # -------- CHECK --------
    if df.empty:
        st.error("❌ Could not parse chat. Please upload correct format.")
        st.stop()

    # -------- CLEAN --------
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    df["Hour"] = pd.to_datetime(df["Time"], errors="coerce").dt.hour

    # -------- EMOJI COUNT --------
    df["Emoji_Count"] = df["Message"].apply(
        lambda x: len(re.findall(r"[^\w\s,]", x))
    )

    # -------- STATS --------
    daily = df.groupby("Date").size()
    hourly = df.groupby("Hour").size()
    user_total = df["User"].value_counts()
    emoji_user = df.groupby("User")["Emoji_Count"].sum()

    total_msgs = len(df)
    avg_per_day = total_msgs // len(daily) if len(daily) > 0 else 0

    # -------- REPORT --------
    st.subheader("📊 REPORT")

    st.write(f"**Total Messages:** {total_msgs}")
    st.write(f"**Average per Day:** {avg_per_day}")

    # 👤 Users
    st.subheader("👤 Users")
    for user, count in user_total.items():
        st.write(f"{user} : {count}")

    # 😂 Emojis
    st.subheader("😂 Emojis")
    for user, count in emoji_user.items():
        st.write(f"{user} : {count}")

    # -------- DAILY COUNTS (NEW IMPROVED) --------
    st.subheader("📅 Daily Message Counts")

    daily_df = daily.reset_index()
    daily_df.columns = ["Date", "Messages"]

    st.dataframe(daily_df)

    # 🔥 Peak Day
    peak_day = daily.idxmax()
    peak_val = daily.max()
    st.success(f"🔥 Peak Day: {peak_day.date()} ({peak_val} messages)")

    # 🏆 Top Days
    st.subheader("🏆 Top 3 Active Days")
    top_days = daily.sort_values(ascending=False).head(3)
    for date, count in top_days.items():
        st.write(f"{date.date()} : {count}")

    # -------- GRAPHS --------
    st.subheader("📈 Graphical Analysis")

    st.subheader("📈 Daily Message Trend")
    st.line_chart(daily)

    st.subheader("👤 Messages per User")
    st.bar_chart(user_total)

    st.subheader("⏰ Activity by Hour")
    st.bar_chart(hourly)

    st.subheader("😂 Emoji Usage")
    st.bar_chart(emoji_user)

    # -------- SUMMARY --------
    st.subheader("🧠 SUMMARY")

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
