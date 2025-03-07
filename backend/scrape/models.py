from typing import List, Dict, Optional
from pydantic import BaseModel


class Perfume(BaseModel):
    url: str
    name: str 
    brand: str
    photo_url: Optional[str] = None
    accords: Optional[List[Dict[str, float]]] = None  # List of dicts with accord names and percentages
    notes: Optional[List[str]] = None
    smells_like: Optional[List[str]] = None
    pros: Optional[List[str]] = None
    cons: Optional[List[str]] = None
    reviews: Optional[List] = None  # List of review dictionaries

    class Config:
        arbitrary_types_allowed = True 


class RedditComment(BaseModel):
    author: Optional[str] = None
    body: Optional[str] = None
    score: Optional[int] = None

class RedditPost(BaseModel):
    title: str
    url: str
    selftext: Optional[str] = None
    score: Optional[int] = None
    num_comments: Optional[int] = None
    subreddit: str
    created_utc: Optional[int] = None
    id: str
    comments: Optional[List[RedditComment]] = None