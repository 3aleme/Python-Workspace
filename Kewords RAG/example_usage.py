#!/usr/bin/env python3
"""
Example usage script for Google Ads Keyword RAG System
Demonstrates various features and use cases
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from keyword_rag import GPTKeywordRAG

def setup_rag_system():
    """Initialize the RAG system with configuration"""
    
    # Get configuration from environment variables
    config = {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "google_ads_config_path": os.getenv("GOOGLE_ADS_CONFIG_PATH", "./google-ads.yaml"),
        "customer_id": os.getenv("GOOGLE_ADS_CUSTOMER_ID"),
        "vector_store_path": "keyword_vector_store"
    }
    
    # Validate configuration
    if not config["openai_api_key"]:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    if not config["customer_id"]:
        raise ValueError("GOOGLE_ADS_CUSTOMER_ID environment variable is required")
    
    # Initialize RAG system
    rag = GPTKeywordRAG(
        openai_api_key=config["openai_api_key"],
        google_ads_config_path=config["google_ads_config_path"],
        customer_id=config["customer_id"],
        vector_store_path=config["vector_store_path"]
    )
    
    return rag

def demo_keyword_ingestion(rag):
    """Demonstrate keyword data ingestion"""
    print("=" * 60)
    print("KEYWORD DATA INGESTION DEMO")
    print("=" * 60)
    
    # Define seed keywords for different industries
    keyword_sets = {
        "Digital Marketing": [
            "digital marketing", "SEO", "PPC advertising", 
            "social media marketing", "content marketing"
        ],
        "E-commerce": [
            "online shopping", "ecommerce platform", "shopify", 
            "product catalog", "payment gateway"
        ],
        "Fitness": [
            "personal trainer", "gym membership", "workout plan", 
            "fitness equipment", "nutrition coaching"
        ]
    }
    
    for industry, keywords in keyword_sets.items():
        print(f"\nIngesting keywords for {industry}...")
        try:
            rag.update_keyword_data(keywords)
            print(f"✅ Successfully added {len(keywords)} seed keywords for {industry}")
        except Exception as e:
            print(f"❌ Error ingesting {industry} keywords: {e}")
    
    # Show database statistics
    stats = rag.get_keyword_stats()
    print(f"\n📊 Database Statistics:")
    print(f"   Total Keywords: {stats.get('total_keywords', 0)}")
    print(f"   Average Search Volume: {stats.get('avg_search_volume', 0):.0f}")
    print(f"   High Volume Keywords (>10k): {stats.get('high_volume_keywords', 0)}")

def demo_basic_queries(rag):
    """Demonstrate basic RAG queries"""
    print("\n" + "=" * 60)
    print("BASIC QUERIES DEMO")
    print("=" * 60)
    
    queries = [
        "What are the top 5 keywords with the highest search volume?",
        "Show me low-competition keywords for digital marketing",
        "Which keywords have the lowest cost per click?",
        "What's the average CPC for fitness-related keywords?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{i}. Query: {query}")
        print("-" * 50)
        try:
            response = rag.query(query, max_keywords=5)
            print(response)
        except Exception as e:
            print(f"❌ Error: {e}")

def demo_advanced_queries(rag):
    """Demonstrate advanced RAG queries with recommendations"""
    print("\n" + "=" * 60)
    print("ADVANCED QUERIES WITH RECOMMENDATIONS")
    print("=" * 60)
    
    advanced_queries = [
        "I have a $500 monthly budget for PPC. Which keywords should I target?",
        "Find opportunities for long-tail keywords in the fitness niche",
        "What keywords should I avoid due to high competition?",
        "Suggest a keyword strategy for a new e-commerce business"
    ]
    
    for i, query in enumerate(advanced_queries, 1):
        print(f"\n{i}. Query: {query}")
        print("-" * 50)
        try:
            response = rag.query(
                query, 
                max_keywords=10, 
                include_recommendations=True
            )
            print(response)
        except Exception as e:
            print(f"❌ Error: {e}")

def demo_competitive_analysis(rag):
    """Demonstrate competitive analysis