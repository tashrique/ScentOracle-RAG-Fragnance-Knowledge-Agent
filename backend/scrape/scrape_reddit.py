import praw
import os
from dotenv import load_dotenv
from variables import SUBREDDITS, SEARCH_TERMS, GUIDE_POSTS
from models import RedditPost, RedditComment
import time
import json
from typing import List
load_dotenv()

class RedditScraper:
    """
    A class for scraping Reddit posts and comments related to perfumes.
    Uses the PRAW library to interact with Reddit's API.
    """
    def __init__(self):
        """
        Initialize the Reddit scraper with API credentials from environment variables.
        """
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT")
        )
        self.subreddits = SUBREDDITS
        self.search_terms = SEARCH_TERMS
        print(f"Successfully connected to Reddit API")



    def fetch_reddit_posts(self):
        """
        Scrape posts from predefined subreddits based on search terms.
        Saves results to a JSON file.
        
        Returns:
            List of scraped posts
        """
        posts = []
        for subreddit in self.subreddits:
            print(f"Scraping {subreddit}...") 
            subreddit = self.reddit.subreddit(subreddit)
            for submission in subreddit.search(query=self.search_terms, limit=None):

                comments = self.scrape_comments(submission)
                post_data = RedditPost(
                    title=submission.title,
                    url=submission.url, 
                    selftext=submission.selftext,
                    score=submission.score,
                    num_comments=submission.num_comments,
                    subreddit=str(subreddit),
                    created_utc=submission.created_utc,
                    id=submission.id,
                    comments=comments
                )
                posts.append(post_data.model_dump())
            time.sleep(10)
            

        with open("../../data/reddit_perfume_discussions.json", "w") as f:
            json.dump(posts, f, indent=2)
    
        print(f"✅ Scraped {len(posts)} posts from Reddit.")


    def scrape_comments(self, submission) -> List[RedditComment]:
        """
        Extract comments from a Reddit submission.
        
        Args:
            submission: A PRAW submission object
            
        Returns:
            List of RedditComment objects
        """
        comments = []
        print(f"Scraping comments for {submission.title}...")
        submission.comments.replace_more(limit=5)
        for comment in submission.comments.list():
            print(f"Comment: {comment.body}")
            # Get author name as string, handling deleted accounts
            author_name = "DELETED"
            if comment.author:
                try:
                    author_name = comment.author.name
                except:
                    author_name = "DELETED"
                    
            comments.append(RedditComment(
                author=author_name,
                body=comment.body,
                score=comment.score))
        return comments


    def fetch_specific_posts(self, post_urls: List[str]):
        """
        Fetch specific Reddit posts or wiki pages by URL.
        Adds them to existing scraped posts.
        
        Args:
            post_urls: List of Reddit post or wiki URLs to scrape
            
        Returns:
            Updated list of all posts
        """
        posts = []
        # Load existing posts
        with open("../../data/reddit_perfume_discussions.json", "r") as f:
            posts = json.load(f)
            
        for url in post_urls:
            try:
                if "/wiki/" in url:
                    # Handle wiki pages
                    parts = url.split("/wiki/")
                    subreddit_name = parts[0].split("/r/")[1]
                    wiki_page = parts[1].rstrip("/")
                    subreddit = self.reddit.subreddit(subreddit_name)
                    wiki_content = subreddit.wiki[wiki_page].content_md
                    
                    posts.append(RedditPost(
                        title=f"Wiki: {wiki_page}",
                        url=url,
                        selftext=wiki_content,
                        score=0,
                        num_comments=0,
                        subreddit=subreddit_name,
                        created_utc=0,
                        id=f"wiki_{wiki_page}",
                        comments=[]
                    ).model_dump())
                else:
                    # Handle regular submissions
                    submission = self.reddit.submission(url=url)
                    comments = self.scrape_comments(submission)
                    posts.append(RedditPost(
                        title=submission.title,
                        url=submission.url, 
                        selftext=submission.selftext,
                        score=submission.score,
                        num_comments=submission.num_comments,
                        subreddit=str(submission.subreddit),
                        created_utc=submission.created_utc,
                        id=submission.id,
                        comments=comments
                    ).model_dump())
            except Exception as e:
                print(f"Error processing URL {url}: {str(e)}")
                continue
            
        # Write back all posts including new ones
        with open("../../data/reddit_perfume_discussions.json", "w") as f:
            json.dump(posts, f, indent=2)
            
        print(f"✅ Added {len(post_urls)} guide posts to discussions.")
        return posts


if __name__ == "__main__":
    scraper = RedditScraper()
    posts = scraper.fetch_reddit_posts()
    specific_posts = scraper.fetch_specific_posts(GUIDE_POSTS)
