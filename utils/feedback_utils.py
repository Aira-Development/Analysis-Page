from pymongo import MongoClient
from collections import Counter

client = MongoClient('mongodb://localhost:27017/')  # Replace with your actual MongoDB URI
db = client['AIRA_NEW_DB']  # Replace with your actual DB name

def get_feedback_summary():
    """
    Returns comprehensive feedback statistics including:
    - Total likes/dislikes
    - Average ratings
    - Sample comments
    - User engagement metrics
    """
    try:
        # Initialize counters
        stats = {
            "likes_count": 0,
            "dislikes_count": 0,
            "total_ratings": 0,
            "avg_rating": 0.0,
            "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            "like_comments": [],
            "dislike_comments": [],
            "users_with_feedback": 0,
            "feedback_timeline": {}
        }

        # Use aggregation for better performance with large datasets
        pipeline = [
            {"$match": {"$or": [{"feedback": {"$exists": True}}, {"daily_feedbacks": {"$exists": True}}]}},
            {"$project": {
                "feedback": 1,
                "daily_feedbacks": 1,
                "month": {"$month": "$_id"}  # For timeline analysis
            }}
        ]

        for doc in db["feedback"].aggregate(pipeline):
            # Process explicit feedback
            for fb in doc.get('feedback', []):
                if fb.get('feedback_type') == 'like':
                    stats["likes_count"] += 1
                    stats["like_comments"].extend(
                        c['text'] for c in fb.get('comments', []) 
                        if c.get('text') and len(stats["like_comments"]) < 10  # Limit to 10 comments
                    )
                elif fb.get('feedback_type') == 'dislike':
                    stats["dislikes_count"] += 1
                    stats["dislike_comments"].extend(
                        c['text'] for c in fb.get('comments', []) 
                        if c.get('text') and len(stats["dislike_comments"]) < 10
                    )

            # Process daily ratings
            for daily in doc.get('daily_feedbacks', []):
                rating = daily.get('rating', 0)
                if 1 <= rating <= 5:
                    stats["total_ratings"] += 1
                    stats["rating_distribution"][rating] += 1

            # Track monthly feedback
            month = doc.get('month')
            if month:
                stats["feedback_timeline"].setdefault(month, 0)
                stats["feedback_timeline"][month] += 1

        # Calculate derived metrics
        stats["users_with_feedback"] = db["feedback"].count_documents({
            "$or": [{"feedback": {"$exists": True, "$ne": []}}, 
                   {"daily_feedbacks": {"$exists": True, "$ne": []}}]
        })

        if stats["total_ratings"] > 0:
            total_score = sum(rating * count for rating, count in stats["rating_distribution"].items())
            stats["avg_rating"] = round(total_score / stats["total_ratings"], 2)

        # Add percentages
        total_feedback = stats["likes_count"] + stats["dislikes_count"]
        if total_feedback > 0:
            stats["like_percentage"] = round((stats["likes_count"] / total_feedback) * 100, 1)
            stats["dislike_percentage"] = round((stats["dislikes_count"] / total_feedback) * 100, 1)

        return stats

    except Exception as e:
        return {
            "error": "Failed to generate feedback summary",
            "details": str(e)
        }


def get_user_feedback(user_id):
    """
    Return all feedback (likes and dislikes) with comments for a specific user.
    """
    doc = db["feedback"].find_one({"_id": user_id})
    if not doc:
        return {
            "likes": [],
            "dislikes": []
        }

    likes = []
    dislikes = []

    for fb in doc.get('feedback', []):
        fb_type = fb.get('feedback_type')
        comments = [c['text'] for c in fb.get('comments', []) if c.get('text')]
        if fb_type == 'like':
            likes.append({
                "response_id": fb.get('response_id'),
                "comments": comments,
                "timestamp": fb.get('timestamp')
            })
        elif fb_type == 'dislike':
            dislikes.append({
                "response_id": fb.get('response_id'),
                "comments": comments,
                "timestamp": fb.get('timestamp')
            })

    return {
        "likes": likes,
        "dislikes": dislikes,
    }
