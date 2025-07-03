import os
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import aiohttp
import pandas as pd
import numpy as np
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.api_core import retry
import openai
from sentence_transformers import SentenceTransformer
import faiss
import pickle
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class KeywordData:
    """Data structure for keyword information"""
    keyword: str
    search_volume: int
    competition: str
    cpc_high: float
    cpc_low: float
    ad_impression_share: float
    top_of_page_cpc_high: float
    top_of_page_cpc_low: float
    currency_code: str
    timestamp: datetime

class GoogleAdsKeywordExtractor:
    """Handles Google Ads API interactions for keyword data extraction"""
    
    def __init__(self, config_path: str):
        """
        Initialize Google Ads client
        
        Args:
            config_path: Path to google-ads.yaml configuration file
        """
        self.client = GoogleAdsClient.load_from_storage(config_path)
        self.customer_id = None
    
    def set_customer_id(self, customer_id: str):
        """Set the Google Ads customer ID"""
        self.customer_id = customer_id.replace('-', '')
    
    def get_keyword_ideas(self, keywords: List[str], location_ids: List[str] = None, 
                         language_id: str = "1000") -> List[KeywordData]:
        """
        Get keyword ideas and metrics from Google Ads API
        
        Args:
            keywords: List of seed keywords
            location_ids: Geographic location IDs (default: None for all locations)
            language_id: Language ID (default: 1000 for English)
            
        Returns:
            List of KeywordData objects
        """
        if not self.customer_id:
            raise ValueError("Customer ID must be set before making API calls")
        
        keyword_plan_idea_service = self.client.get_service("KeywordPlanIdeaService")
        
        request = self.client.get_type("GenerateKeywordIdeasRequest")
        request.customer_id = self.customer_id
        request.language = f"languageConstants/{language_id}"
        
        if location_ids:
            request.geo_target_constants = [f"geoTargetConstants/{loc}" for loc in location_ids]
        
        # Set keyword seed
        request.keyword_seed.keywords.extend(keywords)
        
        # Configure keyword plan network
        request.keyword_plan_network = self.client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
        
        keyword_data_list = []
        
        try:
            response = keyword_plan_idea_service.generate_keyword_ideas(request=request)
            
            for idea in response:
                keyword_data = KeywordData(
                    keyword=idea.text,
                    search_volume=idea.keyword_idea_metrics.avg_monthly_searches or 0,
                    competition=idea.keyword_idea_metrics.competition.name,
                    cpc_high=idea.keyword_idea_metrics.high_top_of_page_bid_micros / 1_000_000 if idea.keyword_idea_metrics.high_top_of_page_bid_micros else 0,
                    cpc_low=idea.keyword_idea_metrics.low_top_of_page_bid_micros / 1_000_000 if idea.keyword_idea_metrics.low_top_of_page_bid_micros else 0,
                    ad_impression_share=0,  # Not available in keyword ideas
                    top_of_page_cpc_high=idea.keyword_idea_metrics.high_top_of_page_bid_micros / 1_000_000 if idea.keyword_idea_metrics.high_top_of_page_bid_micros else 0,
                    top_of_page_cpc_low=idea.keyword_idea_metrics.low_top_of_page_bid_micros / 1_000_000 if idea.keyword_idea_metrics.low_top_of_page_bid_micros else 0,
                    currency_code="USD",  # Default, should be configured based on account
                    timestamp=datetime.now()
                )
                keyword_data_list.append(keyword_data)
                
        except GoogleAdsException as ex:
            logger.error(f"Google Ads API error: {ex}")
            raise
        
        return keyword_data_list

class KeywordVectorStore:
    """Vector store for keyword data using FAISS"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize vector store
        
        Args:
            model_name: SentenceTransformer model name
        """
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.keyword_data = []
        self.embeddings = []
    
    def add_keywords(self, keyword_data_list: List[KeywordData]):
        """Add keyword data to vector store"""
        texts = []
        for kd in keyword_data_list:
            # Create rich text representation for embedding
            text = f"Keyword: {kd.keyword} | Search Volume: {kd.search_volume} | Competition: {kd.competition} | CPC: ${kd.cpc_low:.2f}-${kd.cpc_high:.2f}"
            texts.append(text)
        
        # Generate embeddings
        embeddings = self.model.encode(texts)
        
        if self.index is None:
            # Initialize FAISS index
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add to index
        self.index.add(embeddings.astype(np.float32))
        
        # Store data
        self.keyword_data.extend(keyword_data_list)
        self.embeddings.extend(embeddings)
    
    def search(self, query: str, k: int = 10) -> List[tuple]:
        """
        Search for similar keywords
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of tuples (KeywordData, similarity_score)
        """
        if self.index is None or len(self.keyword_data) == 0:
            return []
        
        # Encode query
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding.astype(np.float32), k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.keyword_data):
                results.append((self.keyword_data[idx], float(score)))
        
        return results
    
    def save(self, path: str):
        """Save vector store to disk"""
        data = {
            'keyword_data': self.keyword_data,
            'embeddings': self.embeddings
        }
        
        # Save FAISS index
        if self.index is not None:
            faiss.write_index(self.index, f"{path}.index")
        
        # Save keyword data
        with open(f"{path}.pkl", 'wb') as f:
            pickle.dump(data, f)
    
    def load(self, path: str):
        """Load vector store from disk"""
        # Load FAISS index
        if os.path.exists(f"{path}.index"):
            self.index = faiss.read_index(f"{path}.index")
        
        # Load keyword data
        if os.path.exists(f"{path}.pkl"):
            with open(f"{path}.pkl", 'rb') as f:
                data = pickle.load(f)
                self.keyword_data = data['keyword_data']
                self.embeddings = data['embeddings']

class GPTKeywordRAG:
    """RAG system combining Google Ads keyword data with GPT"""
    
    def __init__(self, openai_api_key: str, google_ads_config_path: str, 
                 customer_id: str, vector_store_path: str = "keyword_store"):
        """
        Initialize RAG system
        
        Args:
            openai_api_key: OpenAI API key
            google_ads_config_path: Path to Google Ads configuration
            customer_id: Google Ads customer ID
            vector_store_path: Path to save/load vector store
        """
        # Initialize OpenAI
        openai.api_key = openai_api_key
        self.client = openai.OpenAI(api_key=openai_api_key)
        
        # Initialize Google Ads extractor
        self.ads_extractor = GoogleAdsKeywordExtractor(google_ads_config_path)
        self.ads_extractor.set_customer_id(customer_id)
        
        # Initialize vector store
        self.vector_store = KeywordVectorStore()
        self.vector_store_path = vector_store_path
        
        # Load existing data if available
        self._load_existing_data()
    
    def _load_existing_data(self):
        """Load existing vector store data"""
        try:
            self.vector_store.load(self.vector_store_path)
            logger.info(f"Loaded {len(self.vector_store.keyword_data)} keywords from existing store")
        except Exception as e:
            logger.info(f"No existing data found or error loading: {e}")
    
    def update_keyword_data(self, keywords: List[str], location_ids: List[str] = None):
        """
        Update keyword data from Google Ads API
        
        Args:
            keywords: List of seed keywords to expand
            location_ids: Geographic targeting
        """
        logger.info(f"Fetching keyword data for: {keywords}")
        
        try:
            keyword_data = self.ads_extractor.get_keyword_ideas(keywords, location_ids)
            self.vector_store.add_keywords(keyword_data)
            
            # Save updated data
            self.vector_store.save(self.vector_store_path)
            
            logger.info(f"Added {len(keyword_data)} keywords to vector store")
            
        except Exception as e:
            logger.error(f"Error updating keyword data: {e}")
            raise
    
    def _format_keyword_context(self, keyword_results: List[tuple]) -> str:
        """Format keyword data for GPT context"""
        if not keyword_results:
            return "No relevant keyword data found."
        
        context = "Relevant Keyword Data:\n\n"
        
        for i, (keyword_data, score) in enumerate(keyword_results, 1):
            context += f"{i}. Keyword: '{keyword_data.keyword}'\n"
            context += f"   - Search Volume: {keyword_data.search_volume:,} monthly searches\n"
            context += f"   - Competition: {keyword_data.competition}\n"
            context += f"   - CPC Range: ${keyword_data.cpc_low:.2f} - ${keyword_data.cpc_high:.2f}\n"
            context += f"   - Relevance Score: {score:.3f}\n\n"
        
        return context
    
    def query(self, user_query: str, max_keywords: int = 10, 
              include_recommendations: bool = True) -> str:
        """
        Process user query with RAG
        
        Args:
            user_query: User's question about keywords
            max_keywords: Maximum number of keywords to include in context
            include_recommendations: Whether to include strategic recommendations
            
        Returns:
            GPT response with keyword data context
        """
        # Search for relevant keywords
        keyword_results = self.vector_store.search(user_query, k=max_keywords)
        
        # Format context
        keyword_context = self._format_keyword_context(keyword_results)
        
        # Create system prompt
        system_prompt = """You are an expert digital marketing analyst with access to Google Ads keyword data. 
        Use the provided keyword data to answer questions about search volume, competition, costs, and marketing opportunities.
        
        Provide specific, data-driven insights based on the keyword metrics. When making recommendations, 
        consider search volume, competition levels, and cost-per-click data.
        
        If asked about keywords not in the data, suggest related alternatives from the available data."""
        
        # Create user prompt
        user_prompt = f"""User Query: {user_query}

{keyword_context}

Please provide a comprehensive answer based on the keyword data above."""
        
        if include_recommendations:
            user_prompt += "\n\nInclude strategic recommendations for keyword targeting and campaign optimization."
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating GPT response: {e}")
            return f"Error generating response: {e}"
    
    def get_keyword_stats(self) -> Dict[str, Any]:
        """Get statistics about the keyword database"""
        if not self.vector_store.keyword_data:
            return {"total_keywords": 0}
        
        df = pd.DataFrame([
            {
                'keyword': kd.keyword,
                'search_volume': kd.search_volume,
                'competition': kd.competition,
                'cpc_high': kd.cpc_high,
                'cpc_low': kd.cpc_low
            } for kd in self.vector_store.keyword_data
        ])
        
        stats = {
            "total_keywords": len(df),
            "avg_search_volume": df['search_volume'].mean(),
            "median_search_volume": df['search_volume'].median(),
            "avg_cpc": df['cpc_high'].mean(),
            "competition_distribution": df['competition'].value_counts().to_dict(),
            "high_volume_keywords": len(df[df['search_volume'] > 10000]),
            "low_competition_keywords": len(df[df['competition'] == 'LOW'])
        }
        
        return stats

# Example usage and configuration
def main():
    """Example usage of the RAG system"""
    
    # Configuration
    CONFIG = {
        "openai_api_key": "your-openai-api-key",
        "google_ads_config_path": "path/to/google-ads.yaml",
        "customer_id": "your-customer-id",
        "vector_store_path": "keyword_vector_store"
    }
    
    # Initialize RAG system
    rag = GPTKeywordRAG(
        openai_api_key=CONFIG["openai_api_key"],
        google_ads_config_path=CONFIG["google_ads_config_path"],
        customer_id=CONFIG["customer_id"],
        vector_store_path=CONFIG["vector_store_path"]
    )
    
    # Update with seed keywords
    seed_keywords = [
        "digital marketing",
        "SEO services",
        "PPC advertising",
        "social media marketing",
        "content marketing"
    ]
    
    # Fetch and store keyword data
    rag.update_keyword_data(seed_keywords)
    
    # Example queries
    queries = [
        "What are the best low-competition keywords for digital marketing?",
        "Show me high-volume keywords with reasonable CPC costs",
        "Which keywords have the highest search volume?",
        "What's the average cost per click for marketing-related keywords?"
    ]
    
    print("Google Ads Keyword RAG System")
    print("=" * 50)
    
    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 30)
        response = rag.query(query)
        print(response)
        print("\n" + "="*50)
    
    # Show database statistics
    stats = rag.get_keyword_stats()
    print(f"\nKeyword Database Statistics:")
    for key, value in stats.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()