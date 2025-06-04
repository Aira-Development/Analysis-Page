from pymongo import MongoClient
from bson.objectid import ObjectId

client = MongoClient('mongodb://localhost:27017/')  # Replace with your actual MongoDB URI
db = client['AIRA_NEW_DB']  # Replace with your actual DB name

def get_user_detail(user_id):
    """Fetch detailed user info including journals, sentiments, and streak."""
    user = db["users"].find_one({"_id": ObjectId(user_id)})
    if not user:
        return None

    # Fetch sentiments
    sentiments_doc = db["sentiment"].find_one({"user_id": user_id})
    sentiments = sentiments_doc.get('sentiments', []) if sentiments_doc else []

    # You can add more fields as needed

    return {
        "username": user.get("username"),
        "email": user.get("email"),
        "streak": user.get("streak", 0),
        "sentiments": sentiments,
    }
