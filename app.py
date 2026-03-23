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
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall()

        for f in os.listdir():
            if f.endswith(".txt"):
                file_path = f
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

    # -------- DEBUG --------
    st.write("Parsed messages:", len(df))

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
    st.subheader("📌 Key Stats")
    st.write(f"Total Messages: {total_msgs}")
    st.write(f"Average Messages per Day: {avg_per_day}")

    # -------- GRAPHS --------
    st.subheader("📅 Messages per Day")
    st.line_chart(daily)

    st.subheader("👤 Messages per User")
    st.bar_chart(user_total)

    st.subheader("⏰ Activity by Hour")
    st.bar_chart(hourly)

    st.subheader("😂 Emoji Usage")
    st.bar_chart(emoji_user)

    # -------- SMART SUMMARY --------
    st.subheader("🧠 Smart Summary")

    peak_day = daily.idxmax()
    peak_val = daily.max()

    summary = []

    summary.append(f"Peak activity on {peak_day.date()} with {peak_val} messages.")
    summary.append(f"{user_total.idxmax()} is the most active user.")

    if len(user_total) >= 2:
        diff = abs(user_total.iloc[0] - user_total.iloc[1])
        if diff < total_msgs * 0.1:
            summary.append("Conversation is balanced between users.")
        else:
            summary.append("One user dominates the conversation.")

    peak_hour = hourly.idxmax()
    summary.append(f"Most messages are sent around {peak_hour}:00 hours.")
    summary.append(f"Total {total_msgs} messages exchanged.")

    for s in summary:
        st.write("•", s)