import pandas as pd
import re
import zipfile
import os
import streamlit as st

# -------- PAGE CONFIG --------
st.set_page_config(page_title="WhatsApp Analyzer", layout="wide")

# -------- CUSTOM UI --------
st.markdown("""
<style>
.metric-card {
    background: #1c1f26;
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    color: white;
    box-shadow: 0 0 10px rgba(0,0,0,0.5);
}
</style>
""", unsafe_allow_html=True)

# -------- TITLE --------
st.markdown("<h1 style='text-align:center;'>📊 WhatsApp Chat Analyzer 🚀</h1>", unsafe_allow_html=True)

# -------- FILE UPLOAD --------
uploaded_file = st.file_uploader("📂 Upload WhatsApp Chat (.txt or .zip)", type=["txt", "zip"])

if uploaded_file:

    file_path = uploaded_file.name

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # -------- HANDLE ZIP --------
    if file_path.endswith(".zip"):
        st.info("📦 Extracting ZIP file...")
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
        st.error("❌ Could not parse chat. Please upload correct format.")
        st.stop()

    # -------- CLEAN DATA --------
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
    col1.markdown(f"<div class='metric-card'><h3>Total Messages</h3><h1>{total_msgs}</h1></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='metric-card'><h3>Avg / Day</h3><h1>{avg_per_day}</h1></div>", unsafe_allow_html=True)

    st.divider()

    # -------- USERS --------
    st.markdown("## 👤 User Message Distribution")
    st.caption("Total number of messages sent by each user.")
    user_df = user_total.reset_index()
    user_df.columns = ["User", "Messages"]
    st.dataframe(user_df, use_container_width=True)

    # -------- EMOJI --------
    st.markdown("## 😂 Emoji Usage Analysis")
    st.caption("Number of emojis used by each user.")
    emoji_df = emoji_user.reset_index()
    emoji_df.columns = ["User", "Emojis"]
    st.dataframe(emoji_df, use_container_width=True)

    # -------- DAILY --------
    st.markdown("## 📅 Daily Message Counts")
    st.caption("Messages sent per day.")

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

    # -------- GRAPH SECTION --------
    st.markdown("## 📈 Graphical Analysis")
    st.info("These graphs help understand chat activity patterns, user behavior, and engagement trends.")

    # Daily trend
    st.markdown("### 📅 Daily Message Trend (Messages vs Date)")
    st.caption("Shows how chat activity changes over time.")
    st.line_chart(daily)

    # User messages
    st.markdown("### 👤 Messages per User")
    st.caption("Compares total messages sent by each user.")
    st.bar_chart(user_total)

    # Hourly activity
    st.markdown("### ⏰ Activity by Hour (Time vs Messages)")
    st.caption("Shows when users are most active during the day.")
    st.bar_chart(hourly)

    # Emoji usage
    st.markdown("### 😂 Emoji Usage Distribution")
    st.caption("Shows emoji usage comparison between users.")
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
