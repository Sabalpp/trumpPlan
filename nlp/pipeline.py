"""
NLP Pipeline for Political Text Analysis
=======================================

3-Stage Pipeline:
1. Sentiment & Tone Analysis (Transformer-based)
2. Named Entity Recognition (spaCy)
3. Topic Modeling (LDA for sector mapping)

Converts political text → trading signals with explainability
"""

from typing import Dict, List, Optional, Tuple
import warnings

import numpy as np
import pandas as pd
import spacy
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import torch

from data.market import TickerMapper

warnings.filterwarnings('ignore')


class SentimentAnalyzer:
    """
    Stage 1: Sentiment and Tone Analysis using Fine-tuned Transformer
    
    Uses cardiffnlp/twitter-roberta-base-sentiment-latest for political text
    Outputs:
    - Polarity: -1 (negative) to +1 (positive)
    - Tone: Aggressive / Cooperative / Neutral
    """
    
    def __init__(self, model_name: str = 'cardiffnlp/twitter-roberta-base-sentiment-latest'):
        print(f"📦 Loading sentiment model: {model_name}...")
        
        try:
            self.sentiment_pipeline = pipeline(
                'sentiment-analysis',
                model=model_name,
                device=0 if torch.cuda.is_available() else -1
            )
            self.model_loaded = True
        except Exception as e:
            print(f"⚠️  Failed to load transformer model: {str(e)}")
            print("    Falling back to VADER for sentiment")
            self.model_loaded = False
            
            # Fallback to VADER
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self.vader = SentimentIntensityAnalyzer()
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment polarity
        
        Args:
            text: Input text
        
        Returns:
            Dict with label, score, and polarity (-1 to +1)
        """
        if self.model_loaded:
            try:
                # Use transformer
                result = self.sentiment_pipeline(text[:512])[0]  # Truncate to model limit
                
                label = result['label'].lower()
                score = result['score']
                
                # Map to polarity
                if 'positive' in label or 'pos' in label:
                    polarity = score
                elif 'negative' in label or 'neg' in label:
                    polarity = -score
                else:
                    polarity = 0.0
                
                return {
                    'label': label,
                    'score': score,
                    'polarity': round(polarity, 3)
                }
            except Exception as e:
                print(f"⚠️  Transformer analysis failed: {str(e)}")
                # Fallback to VADER
                return self._vader_fallback(text)
        else:
            return self._vader_fallback(text)
    
    def _vader_fallback(self, text: str) -> Dict:
        """Fallback to VADER sentiment"""
        scores = self.vader.polarity_scores(text)
        return {
            'label': 'positive' if scores['compound'] > 0 else 'negative',
            'score': abs(scores['compound']),
            'polarity': scores['compound']
        }
    
    def classify_tone(self, text: str) -> str:
        """
        Classify communication tone
        
        Tone categories:
        - Aggressive: "Cancel", "Fire", "Terminate", "Disaster", "Terrible"
        - Cooperative: "Great", "Wonderful", "Working together", "Partnership"
        - Neutral: Default
        
        Args:
            text: Input text
        
        Returns:
            Tone category
        """
        text_lower = text.lower()
        
        # Keyword-based tone classification (simple but effective for political text)
        aggressive_keywords = [
            'cancel', 'fire', 'terminate', 'disaster', 'terrible', 'worst',
            'fail', 'failing', 'fraud', 'corrupt', 'disgrace', 'incompetent',
            'sue', 'lawsuit', 'investigate', 'criminal'
        ]
        
        cooperative_keywords = [
            'great', 'wonderful', 'fantastic', 'excellent', 'best',
            'working together', 'partnership', 'collaboration', 'ally',
            'congratulations', 'thank', 'appreciate', 'support'
        ]
        
        aggressive_count = sum(1 for kw in aggressive_keywords if kw in text_lower)
        cooperative_count = sum(1 for kw in cooperative_keywords if kw in text_lower)
        
        if aggressive_count > cooperative_count and aggressive_count > 0:
            return 'Aggressive'
        elif cooperative_count > aggressive_count and cooperative_count > 0:
            return 'Cooperative'
        else:
            return 'Neutral'


class EntityExtractor:
    """
    Stage 2: Named Entity Recognition with spaCy
    
    Extracts:
    - Organizations → Stock tickers
    - Money mentions → Magnitude signals
    - Geopolitical entities → Sector implications
    """
    
    def __init__(self, model_name: str = 'en_core_web_sm'):
        print(f"📦 Loading spaCy model: {model_name}...")
        
        try:
            self.nlp = spacy.load(model_name)
            self.model_loaded = True
        except Exception as e:
            print(f"⚠️  Failed to load spaCy model: {str(e)}")
            print(f"    Run: python -m spacy download {model_name}")
            self.model_loaded = False
            self.nlp = None
        
        self.ticker_mapper = TickerMapper()
    
    def extract_entities(self, text: str) -> Dict:
        """
        Extract named entities and map to tickers
        
        Args:
            text: Input text
        
        Returns:
            Dict with organizations, tickers, money, locations
        """
        if not self.model_loaded:
            # Fallback to simple keyword matching
            return self._fallback_extraction(text)
        
        doc = self.nlp(text)
        
        organizations = []
        money = []
        locations = []
        
        for ent in doc.ents:
            if ent.label_ == 'ORG':
                organizations.append(ent.text)
            elif ent.label_ == 'MONEY':
                money.append(ent.text)
            elif ent.label_ in ['GPE', 'LOC']:
                locations.append(ent.text)
        
        # Map organizations to tickers
        tickers = []
        for org in organizations:
            ticker = self.ticker_mapper.map_company_to_ticker(org)
            if ticker:
                tickers.append(ticker)
        
        return {
            'organizations': list(set(organizations)),
            'tickers': list(set(tickers)),
            'money_mentions': money,
            'locations': locations,
            'entity_count': len(doc.ents)
        }
    
    def _fallback_extraction(self, text: str) -> Dict:
        """Simple keyword-based extraction as fallback"""
        # Use TickerMapper's company list
        tickers = []
        organizations = []
        
        for company, ticker in self.ticker_mapper.company_map.items():
            if company in text.lower():
                tickers.append(ticker)
                organizations.append(company.title())
        
        return {
            'organizations': list(set(organizations)),
            'tickers': list(set(tickers)),
            'money_mentions': [],
            'locations': [],
            'entity_count': len(organizations)
        }


class TopicModeler:
    """
    Stage 3: Topic Modeling with LDA
    
    Maps political topics to sectors/ETFs:
    - "Tariffs" → Industrials (XLI)
    - "Tax cuts" → Financials (XLF)
    - "Healthcare" → Healthcare (XLV)
    - "Tech regulation" → Technology (XLK)
    """
    
    def __init__(self, n_topics: int = 10):
        self.n_topics = n_topics
        self.lda_model = None
        self.vectorizer = None
        self.fitted = False
        
        # Topic → Sector/ETF mapping
        self.topic_keywords = {
            'trade_tariffs': {
                'keywords': ['tariff', 'trade', 'import', 'export', 'china', 'manufacturing'],
                'sector': 'Industrials',
                'etf': 'XLI',
                'direction': 'short'  # Tariffs typically negative for manufacturers
            },
            'tax_policy': {
                'keywords': ['tax', 'cut', 'reform', 'corporate', 'revenue'],
                'sector': 'Financials',
                'etf': 'XLF',
                'direction': 'long'  # Tax cuts positive for financials
            },
            'healthcare': {
                'keywords': ['healthcare', 'obamacare', 'medicare', 'pharma', 'drug'],
                'sector': 'Healthcare',
                'etf': 'XLV',
                'direction': 'neutral'
            },
            'tech_regulation': {
                'keywords': ['tech', 'silicon valley', 'social media', 'regulation', 'antitrust'],
                'sector': 'Technology',
                'etf': 'XLK',
                'direction': 'short'  # Regulation negative for tech
            },
            'energy_policy': {
                'keywords': ['energy', 'oil', 'gas', 'pipeline', 'coal', 'drilling'],
                'sector': 'Energy',
                'etf': 'XLE',
                'direction': 'long'  # Pro-fossil fuel rhetoric
            },
            'defense': {
                'keywords': ['defense', 'military', 'pentagon', 'weapons', 'security'],
                'sector': 'Aerospace & Defense',
                'etf': 'ITA',
                'direction': 'long'
            }
        }
    
    def fit(self, corpus: List[str]):
        """
        Fit LDA model on political text corpus
        
        Args:
            corpus: List of political communications
        """
        if len(corpus) < 10:
            print("⚠️  Corpus too small for topic modeling (need 10+ docs)")
            return
        
        # Vectorize
        self.vectorizer = CountVectorizer(
            max_features=1000,
            stop_words='english',
            max_df=0.7,
            min_df=2
        )
        
        doc_term_matrix = self.vectorizer.fit_transform(corpus)
        
        # Fit LDA
        self.lda_model = LatentDirichletAllocation(
            n_components=self.n_topics,
            random_state=42,
            max_iter=50
        )
        
        self.lda_model.fit(doc_term_matrix)
        self.fitted = True
        
        print(f"✓ LDA model fitted on {len(corpus)} documents, {self.n_topics} topics")
    
    def classify_topic(self, text: str) -> Dict:
        """
        Classify text into political topic and map to sector
        
        Args:
            text: Input text
        
        Returns:
            Dict with topic, sector, ETF, and direction
        """
        text_lower = text.lower()
        
        # Score each topic based on keyword matches
        topic_scores = {}
        for topic_name, topic_data in self.topic_keywords.items():
            score = sum(1 for kw in topic_data['keywords'] if kw in text_lower)
            if score > 0:
                topic_scores[topic_name] = score
        
        if not topic_scores:
            return {
                'topic': 'unknown',
                'sector': None,
                'etf': None,
                'direction': 'neutral',
                'confidence': 0.0
            }
        
        # Get top topic
        top_topic = max(topic_scores, key=topic_scores.get)
        top_score = topic_scores[top_topic]
        
        topic_data = self.topic_keywords[top_topic]
        
        # Confidence based on keyword density
        confidence = min(top_score / 5, 1.0)  # Max out at 5 keywords
        
        return {
            'topic': top_topic,
            'sector': topic_data['sector'],
            'etf': topic_data['etf'],
            'direction': topic_data['direction'],
            'confidence': round(confidence, 2)
        }


class NLPPipeline:
    """
    Full 3-stage NLP pipeline for political text → trading signals
    """
    
    def __init__(self):
        print("\n🔧 Initializing NLP Pipeline...\n")
        
        self.sentiment_analyzer = SentimentAnalyzer()
        self.entity_extractor = EntityExtractor()
        self.topic_modeler = TopicModeler()
        
        print("\n✓ NLP Pipeline ready\n")
    
    def process_text(self, text: str, timestamp: Optional[str] = None) -> Dict:
        """
        Process political text through full pipeline
        
        Args:
            text: Political communication text
            timestamp: Optional timestamp for context
        
        Returns:
            Dict with sentiment, entities, topics, and trading signals
        """
        # Stage 1: Sentiment & Tone
        sentiment = self.sentiment_analyzer.analyze_sentiment(text)
        tone = self.sentiment_analyzer.classify_tone(text)
        
        # Stage 2: Entity Extraction
        entities = self.entity_extractor.extract_entities(text)
        
        # Stage 3: Topic Classification
        topic = self.topic_modeler.classify_topic(text)
        
        # Generate trading signals
        signals = self._generate_signals(sentiment, entities, topic, text)
        
        # Build result
        result = {
            'text': text[:200] + ('...' if len(text) > 200 else ''),
            'timestamp': timestamp,
            
            # Sentiment
            'sentiment_polarity': sentiment['polarity'],
            'sentiment_label': sentiment['label'],
            'tone': tone,
            
            # Entities
            'organizations': entities['organizations'],
            'tickers': entities['tickers'],
            'ticker_count': len(entities['tickers']),
            
            # Topic
            'topic': topic['topic'],
            'sector': topic['sector'],
            'sector_etf': topic['etf'],
            'topic_direction': topic['direction'],
            
            # Trading Signals
            'signals': signals,
            'signal_count': len(signals),
            
            # Summary
            'summary': self._generate_summary(sentiment, tone, entities, topic, signals)
        }
        
        return result
    
    def _generate_signals(
        self,
        sentiment: Dict,
        entities: Dict,
        topic: Dict,
        text: str
    ) -> List[Dict]:
        """
        Generate trading signals from NLP outputs
        
        Combines:
        - Sentiment polarity → Direction
        - Mentioned tickers → Specific stock signals
        - Topic → Sector/ETF signals
        """
        signals = []
        
        # Individual stock signals (from mentioned tickers)
        for ticker in entities['tickers']:
            signal_direction = 'long' if sentiment['polarity'] > 0.05 else \
                             'short' if sentiment['polarity'] < -0.05 else 'neutral'
            
            # Tone modulates strength
            strength_multiplier = 1.5 if tone == 'Aggressive' else 1.0
            
            signals.append({
                'type': 'stock',
                'ticker': ticker,
                'direction': signal_direction,
                'confidence': round(abs(sentiment['polarity']) * strength_multiplier, 2),
                'reason': f"{tone} tone, direct mention"
            })
        
        # Sector/ETF signals (from topic classification)
        if topic['etf'] and topic['direction'] != 'neutral':
            # Sector signal
            sector_confidence = topic['confidence'] * 0.7  # Lower confidence for sector plays
            
            signals.append({
                'type': 'sector_etf',
                'ticker': topic['etf'],
                'direction': topic['direction'],
                'confidence': round(sector_confidence, 2),
                'reason': f"Topic: {topic['topic']}"
            })
        
        return signals
    
    def _generate_summary(
        self,
        sentiment: Dict,
        tone: str,
        entities: Dict,
        topic: Dict,
        signals: List[Dict]
    ) -> str:
        """Generate human-readable summary"""
        parts = []
        
        # Sentiment
        parts.append(f"{sentiment['label'].title()} sentiment ({sentiment['polarity']:.2f})")
        
        # Tone
        parts.append(f"{tone} tone")
        
        # Entities
        if entities['tickers']:
            parts.append(f"Mentions: {', '.join(entities['tickers'][:3])}")
        
        # Topic
        if topic['topic'] != 'unknown':
            parts.append(f"Topic: {topic['topic'].replace('_', ' ')}")
        
        # Signals
        if signals:
            parts.append(f"{len(signals)} trading signal(s)")
        
        return " | ".join(parts)


def batch_process_texts(texts: List[str], timestamps: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Process multiple texts in batch
    
    Args:
        texts: List of political texts
        timestamps: Optional list of timestamps
    
    Returns:
        DataFrame with NLP results
    """
    pipeline = NLPPipeline()
    
    results = []
    for i, text in enumerate(texts):
        timestamp = timestamps[i] if timestamps and i < len(timestamps) else None
        result = pipeline.process_text(text, timestamp)
        results.append(result)
    
    df = pd.DataFrame(results)
    return df


if __name__ == '__main__':
    # Test NLP pipeline
    print("\n🧪 Testing NLP Pipeline\n")
    
    # Sample political texts
    test_texts = [
        "Boeing is building a brand new 747 Air Force One for future presidents, but costs are out of control, more than $4 billion. Cancel order!",
        "Just had a very good call with Apple CEO Tim Cook. Discussed many things including how the U.S. has been treated unfairly on trade with China.",
        "General Motors is very counter to what we want. We don't want General Motors to be building plants outside of this country.",
        "We are going to cut taxes massively for the middle class and for businesses. This will create tremendous growth!"
    ]
    
    pipeline = NLPPipeline()
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n{'='*70}")
        print(f"Text {i}: {text[:80]}...")
        print('='*70)
        
        result = pipeline.process_text(text)
        
        print(f"\nSentiment: {result['sentiment_label']} ({result['sentiment_polarity']:.2f})")
        print(f"Tone: {result['tone']}")
        print(f"Tickers: {result['tickers']}")
        print(f"Topic: {result['topic']} → {result['sector_etf']}")
        print(f"\nSignals ({len(result['signals'])}):")
        for sig in result['signals']:
            print(f"  {sig['type']}: {sig['ticker']} - {sig['direction'].upper()} (conf: {sig['confidence']})")
        print(f"\nSummary: {result['summary']}")

