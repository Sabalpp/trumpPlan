"""
Explainability Module for NLP Predictions
========================================

Uses SHAP (SHapley Additive exPlanations) to explain:
- Why a sentiment score was assigned
- Which words/phrases drove the prediction
- Feature importance for transparency

Required for compliance (non-black-box predictions)
"""

from typing import Dict, List, Optional
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import shap

warnings.filterwarnings('ignore')


class SentimentExplainer:
    """
    Explain sentiment predictions using SHAP
    
    For compliance: Users must understand WHY a signal was generated
    """
    
    def __init__(self, model=None, tokenizer=None):
        """
        Initialize explainer
        
        Args:
            model: Transformer model (optional)
            tokenizer: Tokenizer for model (optional)
        """
        self.model = model
        self.tokenizer = tokenizer
        self.explainer = None
        
        if model and tokenizer:
            self._init_shap_explainer()
    
    def _init_shap_explainer(self):
        """Initialize SHAP explainer for transformer model"""
        try:
            # Create SHAP explainer for text
            self.explainer = shap.Explainer(
                self.model,
                self.tokenizer
            )
            print("✓ SHAP explainer initialized")
        except Exception as e:
            print(f"⚠️  SHAP initialization failed: {str(e)}")
            self.explainer = None
    
    def explain_prediction(
        self,
        text: str,
        prediction: Dict,
        method: str = 'simple'
    ) -> Dict:
        """
        Generate explanation for sentiment prediction
        
        Args:
            text: Input text
            prediction: Sentiment prediction dict
            method: 'simple' (keyword-based) or 'shap' (model-based)
        
        Returns:
            Dict with explanation details
        """
        if method == 'shap' and self.explainer:
            return self._shap_explanation(text, prediction)
        else:
            return self._simple_explanation(text, prediction)
    
    def _simple_explanation(self, text: str, prediction: Dict) -> Dict:
        """
        Simple keyword-based explanation
        
        Identifies positive/negative words that influenced the prediction
        """
        # Positive and negative word lists
        positive_words = [
            'great', 'excellent', 'best', 'wonderful', 'fantastic', 'amazing',
            'success', 'winning', 'tremendous', 'beautiful', 'perfect',
            'congratulations', 'proud', 'strong', 'smart', 'good'
        ]
        
        negative_words = [
            'terrible', 'worst', 'bad', 'awful', 'disaster', 'fail', 'failing',
            'sad', 'weak', 'stupid', 'corrupt', 'fraud', 'disgrace',
            'incompetent', 'loser', 'pathetic', 'horrible', 'disgusting'
        ]
        
        text_lower = text.lower()
        words = text_lower.split()
        
        # Find influential words
        found_positive = [w for w in positive_words if w in text_lower]
        found_negative = [w for w in negative_words if w in text_lower]
        
        # Calculate word contribution scores
        word_contributions = {}
        for word in found_positive:
            word_contributions[word] = 0.1  # Positive contribution
        for word in found_negative:
            word_contributions[word] = -0.1  # Negative contribution
        
        # Sort by absolute contribution
        top_words = sorted(
            word_contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:5]
        
        # Generate explanation text
        if prediction['label'] == 'positive':
            explanation = f"Predicted POSITIVE due to: {', '.join(found_positive[:3])}"
        elif prediction['label'] == 'negative':
            explanation = f"Predicted NEGATIVE due to: {', '.join(found_negative[:3])}"
        else:
            explanation = "Neutral language with mixed sentiment"
        
        return {
            'method': 'keyword',
            'explanation': explanation,
            'positive_words': found_positive,
            'negative_words': found_negative,
            'top_contributors': top_words,
            'polarity_score': prediction.get('polarity', 0.0)
        }
    
    def _shap_explanation(self, text: str, prediction: Dict) -> Dict:
        """
        SHAP-based explanation (for transformer models)
        
        Provides word-level contributions using Shapley values
        """
        if not self.explainer:
            return self._simple_explanation(text, prediction)
        
        try:
            # Get SHAP values
            shap_values = self.explainer([text])
            
            # Extract top contributing tokens
            values = shap_values.values[0]
            tokens = shap_values.data[0]
            
            # Get top positive and negative contributors
            token_contributions = list(zip(tokens, values))
            token_contributions.sort(key=lambda x: x[1], reverse=True)
            
            top_positive = [t for t, v in token_contributions if v > 0][:3]
            top_negative = [t for t, v in token_contributions if v < 0][:3]
            
            explanation = f"Key factors: +{', '.join(top_positive)} | -{', '.join(top_negative)}"
            
            return {
                'method': 'shap',
                'explanation': explanation,
                'positive_contributors': top_positive,
                'negative_contributors': top_negative,
                'shap_values': values.tolist(),
                'tokens': tokens
            }
            
        except Exception as e:
            print(f"⚠️  SHAP explanation failed: {str(e)}")
            return self._simple_explanation(text, prediction)
    
    def visualize_explanation(
        self,
        text: str,
        save_path: Optional[str] = None
    ):
        """
        Create visualization of sentiment explanation
        
        Args:
            text: Input text
            save_path: Path to save plot (optional)
        """
        if not self.explainer:
            print("⚠️  Visualization requires SHAP explainer")
            return
        
        try:
            shap_values = self.explainer([text])
            
            # Create plot
            shap.plots.text(shap_values)
            
            if save_path:
                plt.savefig(save_path, bbox_inches='tight', dpi=150)
                print(f"✓ Saved explanation plot to {save_path}")
            else:
                plt.show()
            
        except Exception as e:
            print(f"⚠️  Visualization failed: {str(e)}")


class SignalExplainer:
    """
    Explain complete trading signal generation
    
    Breaks down how text → signal decision was made
    """
    
    @staticmethod
    def explain_signal(nlp_result: Dict, event_study_result: Optional[Dict] = None) -> str:
        """
        Generate human-readable explanation of trading signal
        
        Args:
            nlp_result: Output from NLP pipeline
            event_study_result: Output from event study (optional)
        
        Returns:
            Explanation string
        """
        explanation_parts = []
        
        # 1. Text analysis
        explanation_parts.append(f"**Sentiment Analysis:**")
        explanation_parts.append(
            f"- Polarity: {nlp_result['sentiment_polarity']:.2f} ({nlp_result['sentiment_label']})"
        )
        explanation_parts.append(f"- Tone: {nlp_result['tone']}")
        
        # 2. Entity extraction
        if nlp_result['tickers']:
            explanation_parts.append(f"\n**Mentioned Companies:**")
            for ticker in nlp_result['tickers'][:5]:
                explanation_parts.append(f"- {ticker}")
        
        # 3. Topic classification
        if nlp_result['topic'] != 'unknown':
            explanation_parts.append(f"\n**Topic Classification:**")
            explanation_parts.append(f"- Topic: {nlp_result['topic'].replace('_', ' ').title()}")
            explanation_parts.append(f"- Sector: {nlp_result['sector']}")
            explanation_parts.append(f"- Related ETF: {nlp_result['sector_etf']}")
        
        # 4. Trading signals
        explanation_parts.append(f"\n**Generated Signals ({nlp_result['signal_count']}):**")
        for signal in nlp_result['signals']:
            explanation_parts.append(
                f"- {signal['ticker']}: {signal['direction'].upper()} "
                f"(confidence: {signal['confidence']:.2f}) - {signal['reason']}"
            )
        
        # 5. Event study results (if available)
        if event_study_result:
            explanation_parts.append(f"\n**Historical Analysis (Event Study):**")
            explanation_parts.append(f"- Expected AR: {event_study_result.get('ar_percentage', 0):.2f}%")
            explanation_parts.append(f"- Statistical significance: p={event_study_result.get('p_value', 1):.3f}")
            explanation_parts.append(f"- Beta: {event_study_result.get('beta', 1):.2f}")
        
        # 6. Confidence rationale
        explanation_parts.append(f"\n**Confidence Factors:**")
        confidence_factors = []
        
        if abs(nlp_result['sentiment_polarity']) > 0.5:
            confidence_factors.append("Strong sentiment signal")
        if nlp_result['tone'] == 'Aggressive':
            confidence_factors.append("Aggressive tone increases impact")
        if nlp_result['ticker_count'] > 0:
            confidence_factors.append(f"Direct company mention(s): {nlp_result['ticker_count']}")
        if event_study_result and event_study_result.get('is_significant'):
            confidence_factors.append("Historically significant event type")
        
        if confidence_factors:
            for factor in confidence_factors:
                explanation_parts.append(f"- {factor}")
        else:
            explanation_parts.append("- Low confidence (weak signals)")
        
        return "\n".join(explanation_parts)
    
    @staticmethod
    def generate_disclaimer(signal: Dict) -> str:
        """
        Generate compliance disclaimer for signal
        
        Args:
            signal: Trading signal dict
        
        Returns:
            Disclaimer text
        """
        disclaimer = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  IMPORTANT DISCLAIMER

This signal is for INFORMATIONAL and RESEARCH purposes only.

• NOT personalized investment advice
• NOT a recommendation to buy/sell securities
• Past performance does NOT guarantee future results
• All investing involves RISK of loss
• Consult a licensed financial advisor before trading

Signal Type: {signal.get('type', 'Unknown')}
Ticker: {signal.get('ticker', 'Unknown')}
Confidence: {signal.get('confidence', 0):.0%}

This platform is NOT a registered investment advisor (RIA).
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return disclaimer


def create_explanation_report(
    text: str,
    nlp_result: Dict,
    event_study_result: Optional[Dict] = None
) -> str:
    """
    Create comprehensive explanation report
    
    Args:
        text: Original political text
        nlp_result: NLP pipeline output
        event_study_result: Event study output (optional)
    
    Returns:
        Formatted explanation report
    """
    report = []
    
    report.append("="*70)
    report.append("SIGNAL EXPLANATION REPORT")
    report.append("="*70)
    report.append("")
    
    report.append(f"**Original Text:**")
    report.append(f"{text[:300]}{'...' if len(text) > 300 else ''}")
    report.append("")
    
    # Full signal explanation
    explanation = SignalExplainer.explain_signal(nlp_result, event_study_result)
    report.append(explanation)
    
    report.append("")
    report.append("="*70)
    report.append(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report.append("="*70)
    
    return "\n".join(report)


if __name__ == '__main__':
    # Test explainability
    print("\n🧪 Testing Explainability Module\n")
    
    # Sample prediction
    sample_text = "Boeing is doing terrible work on Air Force One. Costs are out of control! Cancel the order!"
    sample_prediction = {
        'label': 'negative',
        'score': 0.95,
        'polarity': -0.85
    }
    
    explainer = SentimentExplainer()
    
    explanation = explainer.explain_prediction(sample_text, sample_prediction)
    
    print("Explanation:")
    print(f"  Method: {explanation['method']}")
    print(f"  Text: {explanation['explanation']}")
    print(f"  Positive words: {explanation['positive_words']}")
    print(f"  Negative words: {explanation['negative_words']}")
    print(f"  Top contributors: {explanation['top_contributors']}")
    
    # Test signal explanation
    print("\n" + "="*70)
    print("Signal Explanation Test")
    print("="*70 + "\n")
    
    mock_nlp_result = {
        'text': sample_text,
        'sentiment_polarity': -0.85,
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
                'reason': 'Aggressive tone, direct mention'
            }
        ],
        'signal_count': 1
    }
    
    full_explanation = SignalExplainer.explain_signal(mock_nlp_result)
    print(full_explanation)
    
    # Test disclaimer
    print("\n" + "="*70)
    print("Disclaimer Test")
    print("="*70)
    
    disclaimer = SignalExplainer.generate_disclaimer(mock_nlp_result['signals'][0])
    print(disclaimer)

