# **ScentOracle 🌸💨✨ - Perfume Replica Knowledge RAG**

## **1. Project Overview**
**ScentOracle** is a Retrieval-Augmented Generation (RAG) system designed to help fragrance enthusiasts discover and compare **perfume clones, dupes, and niche fragrances**. It integrates **Reddit discussions**, structured fragrance databases, and price tracking to provide AI-driven insights on perfume alternatives.

## **2. Core Features**
### **Knowledge Base & Retrieval**
- [ ] **Curated Perfume Data**: Indexed information from clone brands (e.g., Lattafa, Afnan, Armaf, Dua, Alexandria Fragrances).
- [ ] **Reddit Insights**: Scraped discussions from `r/fragrance`, `r/fragranceclones`, and related subreddits.
- [ ] **Fragrance Note Breakdown**: Extracting and categorizing top/mid/base notes from user-generated content.
- [ ] **Price Comparisons**: Fetching perfume prices from online fragrance retailers.

### **AI-Powered Q&A**
- [ ] **Clone Finder**: "What's a good alternative to Creed Aventus under $50?"
- [ ] **Scent Profile Matcher**: Suggest perfumes based on user preferences.
- [ ] **Summarized User Opinions**: AI-driven summaries of Reddit discussions.
- [ ] **Historical Price Insights**: Tracking perfume price trends.

## **3. Tech Stack & Budget Considerations**
| Component          | Tool/Service       | Cost Consideration |
|-------------------|-------------------|-------------------|
| **Backend**      | FastAPI            | Free |
| **Frontend**     | Next.js (Vercel)   | Free |
| **Vector DB**    | FAISS (Local)      | Free |
| **Data Source**  | Pushshift API, Scrapy | Free |
| **AI Model**     | GPT-4-Turbo (OpenAI) | $5-10 Budget |
| **Hosting**      | Render/Vercel      | Free |
| **Database**     | SQLite/MongoDB Free | Free |

## **4. Development Roadmap (2 Weeks)**
### **Week 1: Data Collection & Backend Setup**
✅ **Day 1-2:**
- [x]  Set up project structure (FastAPI backend, Next.js frontend, SQLite DB).
- [ ]  Write scripts to scrape fragrance websites

✅ **Day 3-4:**
- [x] Implement **Reddit data fetching** (Pushshift API + Scrapy for comments).
- [ ] Store **structured fragrance data** in FAISS for retrieval.

✅ **Day 5-7:**
- [ ] Implement **vector embedding model** (OpenAI `text-embedding-ada-002`).
- [ ] Create **retrieval pipeline** (query FAISS for relevant clone recommendations).

### **Week 2: AI Integration & Frontend**
✅ **Day 8-9:**
- [ ] Implement **GPT-4 Turbo query processing**.
- [ ] Integrate **retrieved perfume data into AI-generated responses**.

✅ **Day 10-11:**
- [ ] Develop a **basic frontend UI** (Next.js with search and recommendations).
- [ ] Connect frontend with the FastAPI backend.

✅ **Day 12-13:**
- [ ] Deploy backend on **Render** (or Railway if needed).
- [ ] Deploy frontend on **Vercel**.

✅ **Day 14:**
- [ ] Final testing, bug fixes, and optimizations.
- [ ] Prepare documentation and future improvements.

---
### **Next Steps & Expansion Ideas**
- [ ] Add **community voting** to rank fragrance alternatives.
- [ ] Implement **user accounts** for personalized recommendations.
- [ ] Expand **data sources** (YouTube fragrance reviews, additional retailer APIs).

This plan ensures a fully functional **Perfume Knowledge RAG** within **2 weeks**, staying within the **$10 budget** while leveraging free-tier services. 🚀
