"""
Tests for NLP Pipeline
=====================

Tests for:
- nlp/pipeline.py (sentiment, NER, topic modeling)
- nlp/explainability.py (SHAP explanations)
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch

from nlp.pipeline import (
    SentimentAnalyzer,
    EntityExtractor,
    TopicModeler,
    NLPPipeline,
    batch_process_texts
)
from nlp.explainability import (
    SentimentExplainer,
    SignalExplainer,
    create_explanation_report
)


class TestSentimentAnalyzer:
    """Test sentiment analysis"""
    
    def test_initialization(self):
        """Test analyzer initialization"""
        analyzer = SentimentAnalyzer()
        assert analyzer is not None
    
    def test_analyze_positive_sentiment(self):
        """Test positive sentiment detection"""
        analyzer = SentimentAnalyzer()
        text = "This is wonderful news! Apple is doing great things."
        
        result = analyzer.analyze_sentiment(text)
        
        assert 'label' in result
        assert 'polarity' in result
        assert result['polarity'] > 0  # Should be positive
    
    def test_analyze_negative_sentiment(self):
        """Test negative sentiment detection"""
        analyzer = SentimentAnalyzer()
        text = "This is terrible! The worst disaster ever!"
        
        result = analyzer.analyze_sentiment(text)
        
        assert result['polarity'] < 0  # Should be negative
    
    def test_classify_tone_aggressive(self):
        """Test aggressive tone classification"""
        analyzer = SentimentAnalyzer()
        text = "Cancel the order! This is a disaster! Fire everyone!"
        
        tone = analyzer.classify_tone(text)
        
        assert tone == 'Aggressive'
    
    def test_classify_tone_cooperative(self):
        """Test cooperative tone classification"""
        analyzer = SentimentAnalyzer()
        text = "Great working together! Wonderful partnership! Thank you!"
        
        tone = analyzer.classify_tone(text)
        
        assert tone == 'Cooperative'
    
    def test_classify_tone_neutral(self):
        """Test neutral tone classification"""
        analyzer = SentimentAnalyzer()
        text = "The meeting occurred at 3pm. Data was discussed."
        
        tone = analyzer.classify_tone(text)
        
        assert tone == 'Neutral'


class TestEntityExtractor:
    """Test named entity recognition"""
    
    def test_initialization(self):
        """Test extractor initialization"""
        extractor = EntityExtractor()
        assert extractor is not None
    
    def test_extract_entities_with_ticker(self):
        """Test entity extraction with company mentions"""
        extractor = EntityExtractor()
        text = "Boeing is building a new aircraft for the government."
        
        result = extractor.extract_entities(text)
        
        assert 'organizations' in result
        assert 'tickers' in result
        assert 'BA' in result['tickers'] or 'Boeing' in text.lower()
    
    def test_extract_multiple_companies(self):
        """Test multiple company extraction"""
        extractor = EntityExtractor()
        text = "Apple and Microsoft are working together on this project."
        
        result = extractor.extract_entities(text)
        
        # Should find at least one ticker
        assert len(result['tickers']) >= 1
    
    def test_extract_no_entities(self):
        """Test text with no entities"""
        extractor = EntityExtractor()
        text = "This is a generic statement with no companies."
        
        result = extractor.extract_entities(text)
        
        assert isinstance(result['tickers'], list)
        assert isinstance(result['organizations'], list)


class TestTopicModeler:
    """Test topic modeling"""
    
    def test_initialization(self):
        """Test topic modeler initialization"""
        modeler = TopicModeler()
        assert modeler.n_topics == 10
    
    def test_classify_trade_topic(self):
        """Test trade/tariff topic classification"""
        modeler = TopicModeler()
        text = "We are imposing new tariffs on China to protect American manufacturing."
        
        result = modeler.classify_topic(text)
        
        assert result['topic'] in ['trade_tariffs', 'unknown']
        if result['topic'] == 'trade_tariffs':
            assert result['etf'] == 'XLI'
    
    def test_classify_tax_topic(self):
        """Test tax policy topic classification"""
        modeler = TopicModeler()
        text = "We are cutting corporate taxes to boost economic growth."
        
        result = modeler.classify_topic(text)
        
        assert result['topic'] in ['tax_policy', 'unknown']
    
    def test_classify_energy_topic(self):
        """Test energy topic classification"""
        modeler = TopicModeler()
        text = "We support American oil and gas drilling for energy independence."
        
        result = modeler.classify_topic(text)
        
        assert result['topic'] in ['energy_policy', 'unknown']
        if result['topic'] == 'energy_policy':
            assert result['etf'] == 'XLE'
            assert result['direction'] == 'long'
    
    def test_classify_unknown_topic(self):
        """Test unknown topic handling"""
        modeler = TopicModeler()
        text = "Random text with no political keywords."
        
        result = modeler.classify_topic(text)
        
        assert result['topic'] == 'unknown'
        assert result['confidence'] == 0.0


class TestNLPPipeline:
    """Test full NLP pipeline"""
    
    def test_initialization(self):
        """Test pipeline initialization"""
        pipeline = NLPPipeline()
        assert pipeline.sentiment_analyzer is not None
        assert pipeline.entity_extractor is not None
        assert pipeline.topic_modeler is not None
    
    def test_process_text_basic(self):
        """Test basic text processing"""
        pipeline = NLPPipeline()
        text = "Boeing is doing great work on the new aircraft."
        
        result = pipeline.process_text(text)
        
        # Check all expected keys
        assert 'sentiment_polarity' in result
        assert 'tone' in result
        assert 'tickers' in result
        assert 'topic' in result
        assert 'signals' in result
        assert 'summary' in result
    
    def test_process_text_with_timestamp(self):
        """Test processing with timestamp"""
        pipeline = NLPPipeline()
        text = "Apple announces new product."
        timestamp = "2024-01-01T12:00:00Z"
        
        result = pipeline.process_text(text, timestamp)
        
        assert result['timestamp'] == timestamp
    
    def test_generate_signals(self):
        """Test signal generation"""
        pipeline = NLPPipeline()
        text = "Boeing is doing terrible work. Cancel the order!"
        
        result = pipeline.process_text(text)
        
        assert 'signals' in result
        assert len(result['signals']) > 0
        
        # Check signal structure
        for signal in result['signals']:
            assert 'type' in signal
            assert 'ticker' in signal
            assert 'direction' in signal
            assert 'confidence' in signal
    
    def test_positive_signal_generation(self):
        """Test positive signal generation"""
        pipeline = NLPPipeline()
        text = "Apple is doing fantastic work! Best company ever!"
        
        result = pipeline.process_text(text)
        
        # Should have positive sentiment
        assert result['sentiment_polarity'] > 0
        
        # Should generate long signals
        stock_signals = [s for s in result['signals'] if s['type'] == 'stock']
        if stock_signals:
            # At least one should be long
            assert any(s['direction'] == 'long' for s in stock_signals)
    
    def test_negative_signal_generation(self):
        """Test negative signal generation"""
        pipeline = NLPPipeline()
        text = "Boeing is a disaster! Worst company! Cancel everything!"
        
        result = pipeline.process_text(text)
        
        # Should have negative sentiment
        assert result['sentiment_polarity'] < 0
        
        # Should generate short signals
        stock_signals = [s for s in result['signals'] if s['type'] == 'stock']
        if stock_signals:
            # At least one should be short
            assert any(s['direction'] == 'short' for s in stock_signals)


class TestBatchProcessing:
    """Test batch text processing"""
    
    def test_batch_process_multiple_texts(self):
        """Test processing multiple texts"""
        texts = [
            "Apple is doing great work.",
            "Boeing has major problems.",
            "Microsoft announces new partnership."
        ]
        
        df = batch_process_texts(texts)
        
        assert len(df) == 3
        assert 'sentiment_polarity' in df.columns
        assert 'tickers' in df.columns
    
    def test_batch_process_with_timestamps(self):
        """Test batch processing with timestamps"""
        texts = ["Apple news.", "Boeing update."]
        timestamps = ["2024-01-01T10:00:00Z", "2024-01-01T11:00:00Z"]
        
        df = batch_process_texts(texts, timestamps)
        
        assert len(df) == 2
        assert df['timestamp'].tolist() == timestamps


class TestSentimentExplainer:
    """Test sentiment explainability"""
    
    def test_initialization(self):
        """Test explainer initialization"""
        explainer = SentimentExplainer()
        assert explainer is not None
    
    def test_simple_explanation_positive(self):
        """Test simple explanation for positive sentiment"""
        explainer = SentimentExplainer()
        text = "This is great and wonderful work!"
        prediction = {'label': 'positive', 'polarity': 0.8}
        
        explanation = explainer.explain_prediction(text, prediction, method='simple')
        
        assert 'positive_words' in explanation
        assert len(explanation['positive_words']) > 0
        assert 'great' in explanation['positive_words'] or 'wonderful' in explanation['positive_words']
    
    def test_simple_explanation_negative(self):
        """Test simple explanation for negative sentiment"""
        explainer = SentimentExplainer()
        text = "This is terrible and awful work!"
        prediction = {'label': 'negative', 'polarity': -0.8}
        
        explanation = explainer.explain_prediction(text, prediction, method='simple')
        
        assert 'negative_words' in explanation
        assert len(explanation['negative_words']) > 0
    
    def test_explanation_method(self):
        """Test explanation includes method used"""
        explainer = SentimentExplainer()
        text = "Sample text"
        prediction = {'label': 'neutral', 'polarity': 0.0}
        
        explanation = explainer.explain_prediction(text, prediction)
        
        assert 'method' in explanation
        assert explanation['method'] in ['keyword', 'shap']


class TestSignalExplainer:
    """Test trading signal explainability"""
    
    def test_explain_signal(self):
        """Test signal explanation generation"""
        nlp_result = {
            'sentiment_polarity': -0.8,
            'sentiment_label': 'negative',
            'tone': 'Aggressive',
            'tickers': ['BA'],
            'ticker_count': 1,
            'topic': 'defense',
            'sector': 'Aerospace & Defense',
            'sector_etf': 'ITA',
            'signals': [
                {
                    'type': 'stock',
                    'ticker': 'BA',
                    'direction': 'short',
                    'confidence': 0.85,
                    'reason': 'Aggressive tone'
                }
            ],
            'signal_count': 1
        }
        
        explanation = SignalExplainer.explain_signal(nlp_result)
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert 'Sentiment Analysis' in explanation or 'sentiment' in explanation.lower()
        assert 'BA' in explanation
    
    def test_generate_disclaimer(self):
        """Test disclaimer generation"""
        signal = {
            'type': 'stock',
            'ticker': 'AAPL',
            'direction': 'long',
            'confidence': 0.75
        }
        
        disclaimer = SignalExplainer.generate_disclaimer(signal)
        
        assert isinstance(disclaimer, str)
        assert 'DISCLAIMER' in disclaimer
        assert 'NOT' in disclaimer or 'not' in disclaimer
        assert 'AAPL' in disclaimer


class TestExplanationReport:
    """Test explanation report generation"""
    
    def test_create_explanation_report(self):
        """Test full explanation report"""
        text = "Boeing has major issues with Air Force One project."
        
        nlp_result = {
            'sentiment_polarity': -0.7,
            'sentiment_label': 'negative',
            'tone': 'Neutral',
            'tickers': ['BA'],
            'ticker_count': 1,
            'topic': 'defense',
            'sector': 'Aerospace & Defense',
            'sector_etf': 'ITA',
            'signals': [
                {
                    'type': 'stock',
                    'ticker': 'BA',
                    'direction': 'short',
                    'confidence': 0.7,
                    'reason': 'Negative sentiment'
                }
            ],
            'signal_count': 1
        }
        
        report = create_explanation_report(text, nlp_result)
        
        assert isinstance(report, str)
        assert len(report) > 100  # Should be substantial
        assert 'EXPLANATION' in report or 'explanation' in report.lower()
        assert text[:50] in report  # Should include original text


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_text(self):
        """Test handling of empty text"""
        pipeline = NLPPipeline()
        
        result = pipeline.process_text("")
        
        assert result is not None
        assert 'sentiment_polarity' in result
    
    def test_very_long_text(self):
        """Test handling of very long text"""
        pipeline = NLPPipeline()
        long_text = "Apple is great. " * 1000  # Very long text
        
        result = pipeline.process_text(long_text)
        
        assert result is not None
        assert 'tickers' in result
    
    def test_no_company_mentions(self):
        """Test text with no company mentions"""
        pipeline = NLPPipeline()
        text = "This is a generic political statement with no companies."
        
        result = pipeline.process_text(text)
        
        assert result is not None
        assert isinstance(result['tickers'], list)
        assert len(result['tickers']) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

