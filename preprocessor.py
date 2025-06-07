import re
import pandas as pd
from datetime import datetime

def preprocess(data):
    # Normalize non-breaking and narrow spaces
    data = data.replace('\u202f', ' ').replace('\u00a0', ' ')

    # Match dates in both dd/mm/yy and dd/mm/yyyy with AM/PM
    pattern = r'(\d{1,2}/\d{1,2}/(?:\d{2}|\d{4}), \d{1,2}:\d{2} [APap][Mm]) - (.*)'

    matches = re.findall(pattern, data)
    dates = [match[0] for match in matches]
    messages = [match[1] for match in matches]

    df = pd.DataFrame({'user_message': messages, 'message_date': dates})

    # Flexible datetime parsing
    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, '%m/%d/%Y, %I:%M %p')
        except:
            try:
                return datetime.strptime(date_str, '%m/%d/%y, %I:%M %p')
            except:
                return pd.NaT

    df['message_date'] = df['message_date'].apply(parse_date)
    df.rename(columns={'message_date': 'date'}, inplace=True)

    # Split user from message
    users = []
    msgs = []
    for msg in df['user_message']:
        entry = re.split(r'^([^:]+):\s', msg, maxsplit=1)
        if len(entry) == 3:
            users.append(entry[1])
            msgs.append(entry[2])
        else:
            users.append("group_notification")
            msgs.append(entry[0])

    df['user'] = users
    df['message'] = msgs
    df.drop(columns=['user_message'], inplace=True)

    # Clean message text
    df['message'] = df['message'].str.strip().str.lower()

    # Normalize media messages
    df['message'] = df['message'].replace(
        to_replace=[
            r"<media omitted>", r"media omitted", r"image omitted",
            r"photo omitted", r"‎media omitted", r"null",
            r"media हटाइएको छ", r"photo हटाइएको छ"
        ],
        value="media",
        regex=True
    )

    # Add media flag column
    df['is_media'] = df['message'] == "media"

    # Time-based features
    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute

    # Create hour period (e.g., 09-10)
    df['period'] = df['hour'].apply(
        lambda h: f'{int(h):02d}-{(int(h) + 1) % 24:02d}' if pd.notna(h) else 'unknown'
    )

    return df
