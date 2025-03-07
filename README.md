# 🌸💨 ScentOracle: RAG Fragrance Knowledge Agent

[![Maintainability](https://api.codeclimate.com/v1/badges/cb21ea416335b602fe72/maintainability)](https://codeclimate.com/github/tashrique/ScentOracle-RAG-Fragnance-Knowledge-Agent/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/cb21ea416335b602fe72/test_coverage)](https://codeclimate.com/github/tashrique/ScentOracle-RAG-Fragnance-Knowledge-Agent/test_coverage)

## Try the app: [Under Construction](www.tashrique.com)

## 🔍 Overview
ScentOracle-RAG is a **Retrieval-Augmented Generation (RAG) system** that collects and analyzes **perfume data** from **popular websites and Reddit**. The goal is to build a **structured knowledge base** for fragrance clones, dupes, and alternatives.

## ✨ Features
- **Web Scraping**: Extracts fragrance details (notes, accords, reviews) from **popular perfume websites**.
- **Reddit Data Mining**: Fetches relevant discussions and comments using **PRAW** (Reddit API).
- **Knowledge Structuring**: Organizes data into a **queryable format** for AI-enhanced retrieval.

## 🏛️ Project Structure
```
ScentOracle/
├── backend/
│   ├── scrape/
│   │   ├── __init__.py
│   │   ├── models.py           # Pydantic models for data validation
│   │   ├── scrape_reddit.py    # Reddit scraping functionality
│   │   ├── scrape_sites.py     # Website scraping functionality
│   │   └── variables.py        # Configuration variables
│   │
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── clean_data.py       # Data cleaning and preprocessing
│   │   └── embeddings.py       # Text embedding generation
│   │
│   └── api/
│       ├── __init__.py
│       ├── main.py             # FastAPI application
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── perfumes.py     # Perfume-related endpoints
│       │   └── recommendations.py  # Recommendation endpoints
│       └── utils/
│           ├── __init__.py
│           └── helpers.py       # Helper functions
│
├── data/
│   ├── raw/                    # Raw scraped data
│   │   ├── reddit_perfume_discussions.json
│   │   ├── website_designer_links.txt
│   │   └── website_perfumes_by_designer.json
│   │
│   ├── processed/             # Cleaned and processed data
│   │   ├── perfumes.json
│   │   └── embeddings/
│   │       ├── perfume_embeddings.npy
│   │       └── text_embeddings.npy
│   │
│   └── models/               # Trained models and vectors
│       └── sentence_transformers/
│
├── notebooks/
│   ├── data_exploration.ipynb
│   └── model_development.ipynb
│
├── tests/
│   ├── __init__.py
│   ├── test_scraping.py
│   ├── test_processing.py
│   └── test_api.py
│
├── .env                      # Environment variables
├── .gitignore               # Git ignore file
├── requirements.txt         # Python dependencies
├── README.md               # Project documentation
└── setup.py               # Package setup file
```

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- pip (Python package manager)

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/scentoracle-rag.git
   cd scentoracle-rag
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv frag-venv
   source frag-venv/bin/activate  # On Windows: frag-venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys and configuration
   ```

## 🚀 Usage

### Data Collection

1. Scrape Reddit discussions:
   ```bash
   python backend/scrape/scrape_reddit.py
   ```

2. Scrape Fragnance websites data:
   ```bash
   python backend/scrape/scrape_sites.py
   ```

### API Server

1. Start the FastAPI server:
   ```bash
   uvicorn backend.api.main:app --reload
   ```

2. Access the API documentation at `http://localhost:8000/docs`

## 💻 Development

### Running Tests
```bash
pytest tests/
```

### Code Style
We follow PEP 8 guidelines. Format code using:
```bash
black backend/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

Your Name - [Tashrique Ahmed](https://www.linkedin.com/in/tashrique-ahmed/)
Project Link: [https://github.com/tashrique/ScentOracle-RAG-Fragnance-Knowledge-Agent](https://github.com/tashrique/ScentOracle-RAG-Fragnance-Knowledge-Agent)
