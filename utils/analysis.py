from pymongo import MongoClient
from datetime import datetime, timedelta
from collections import Counter

client = MongoClient('mongodb://localhost:27017/')  # Replace with your actual MongoDB URI
db = client['AIRA_NEW_DB']  # Replace with your actual DB name


def get_dashboard_summary():
    today = datetime.utcnow().date()
    users = list(db["users"].find())
    journals = list(db["journal"].find())
    sentiments = list(db["sentiment"].find())

    # Active Users Today
    active_users_today = sum(
        any(journal['date'] == today.isoformat() for journal in user_doc.get('journals', []))
        for user_doc in journals
    )

    # Most Common Mood
    moods = [s['emotional_state'] for s in sum([doc['sentiments'] for doc in sentiments], []) if s['date'] == today.isoformat()]
    most_common_mood = Counter(moods).most_common(1)[0][0] if moods else "Neutral"

    # Avg. Mental Score
    scores = [s['mental_score'] for s in sum([doc['sentiments'] for doc in sentiments], []) if s['date'] == today.isoformat()]
    avg_score = round(sum(scores) / len(scores), 2) if scores else None

    return {
        'active_users_today': active_users_today,
        'most_common_mood': most_common_mood,
        'avg_mental_score': avg_score
    }

def get_mental_health_data():
    sentiments = list(db["sentiment"].find())
    users = list(db["users"].find())
    user_data = []

    # print(f"Total users: {len(users)}, Total sentiment docs: {len(sentiments)}")

    for user in users:
        uid = str(user['_id'])
        name = user.get('username', 'Unknown')
        streak = user.get('streak', 0)

        # Get sentiment entry for user
        sentiment_doc = next((s for s in sentiments if s['user_id'] == uid), None)
        if not sentiment_doc or not sentiment_doc.get('sentiments'):
            continue

        user_sentiments = sentiment_doc['sentiments']
        sorted_sentiments = sorted(user_sentiments, key=lambda x: x['date'])

        latest_score = sorted_sentiments[-1]['mental_score']
        if len(sorted_sentiments) >= 2:
            score_diff = latest_score - sorted_sentiments[-2]['mental_score']
        else:
            score_diff = 0

        common_mood = Counter([s['emotional_state'] for s in user_sentiments]).most_common(1)[0][0]

        user_data.append({
            'username': name,
            'user_id': uid,
            'current_score': round(latest_score, 2),
            'score_diff': round(score_diff, 2),
            'streak': streak,
            'common_mood': common_mood
        })

    # Sort by users with most decline in mental health
    user_data = sorted(user_data, key=lambda x: x['score_diff'])
    return user_data

def get_usage_data():
    journals = list(db["journal"].find())
    users = list(db["users"].find())
    usage_stats = []

    for user in users:
        uid = str(user['_id'])
        name = user['username']

        # Find total messages sent by user
        user_journal = next((doc for doc in journals if doc['user_id'] == uid), None)
        if not user_journal:
            continue

        total_messages = sum(
            1 for journal in user_journal.get('journals', [])
            for msg in journal.get('messages', []) if msg['role'] == 'User'
        )

        last_active = max(
            (msg['created_at'] for journal in user_journal.get('journals', []) for msg in journal.get('messages', []) if msg['role'] == 'User'),
            default="N/A"
        )

        usage_stats.append({
            'username': name,
            'user_id': uid,
            'total_messages': total_messages,
            'last_active': last_active
        })

    usage_stats = sorted(usage_stats, key=lambda x: x['total_messages'], reverse=True)
    return usage_stats