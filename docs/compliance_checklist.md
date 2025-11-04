# Compliance Checklist for Political Sentiment Alpha Platform

**Version**: 0.1.0-MVP  
**Date**: November 3, 2025  
**Status**: Pre-Launch Review

---

## 1. Investment Advisor Registration (IAA 1940)

### ✅ Exclusions Applied

- [ ] **General Information Only**: Platform provides only general, non-personalized signals
- [ ] **No Individual Advice**: No individualized recommendations based on user-specific circumstances
- [ ] **No Discretionary Management**: Platform does not manage user funds
- [ ] **No Fiduciary Relationship**: Explicit disclaimers establish no advisor-client relationship

**Rationale**: Platform falls under **exclusion for publishers of general circulation** (Section 202(a)(11)(D))

**Supporting Documentation**:
- Disclaimer on every page (see `templates/disclaimer.html`)
- No collection of portfolio data or financial situation
- No personalized sign-off or endorsement of specific trades

---

## 2. Securities Act of 1933 (Offer/Sale of Securities)

### ✅ Not Applicable

- Platform does NOT offer/sell securities
- Signals are informational, not solicitations
- No securities transactions occur on platform

---

## 3. Securities Exchange Act of 1934 (Broker-Dealer Rules)

### ✅ Not Applicable

- Platform does NOT execute trades
- Users trade through their own brokerage accounts
- No custody of client assets
- No commissions on trades

---

## 4. Investment Company Act of 1940

### ✅ Not Applicable

- Platform is not a pooled investment vehicle
- No commingling of client funds
- Users invest individually via personal accounts

---

## 5. Gramm-Leach-Bliley Act (GLBA) - Privacy

### ⚠️ Limited Applicability

**Non-Covered Entity** (likely):
- Platform is not a "financial institution" under GLBA
- Does not collect "nonpublic personal information" (NPI) related to financial services

**If Covered (Conservative Approach)**:
- [x] Privacy Policy posted (`docs/privacy.md`)
- [ ] Annual privacy notice (only if significant NPI collected)
- [x] Opt-out for data sharing (we don't share, so no opt-out needed)
- [x] Safeguards Rule: Encryption, access controls, security monitoring

---

## 6. SEC Rule 506(c) - General Solicitation

### ✅ Compliant

- Platform is public (not limited to accredited investors)
- No private securities offerings
- All content is general information

---

## 7. Anti-Fraud Provisions (Section 10(b), Rule 10b-5)

### ✅ Compliance Measures

- [x] **No Misleading Statements**: Clear disclaimers about risks, no guarantees
- [x] **Material Facts Disclosed**: Disclaimer includes model limitations, data sources
- [x] **No Manipulation**: Platform does not coordinate trading or manipulate prices
- [x] **Transparency**: Explainability module shows reasoning behind signals

**Key Requirement**: Signals must not be intentionally misleading or omit material facts

**Implemented**:
- Every signal includes confidence score and explanation
- Disclaimers on all pages
- No "guaranteed returns" language

---

## 8. Advertising Rules (Investment Advisers Act Rule 206(4)-1)

### ⚠️ If Deemed Investment Advice

**Conservative Compliance** (apply even if not RIA):
- [x] No testimonials without disclosures
- [x] No performance claims without caveats ("past performance...")
- [ ] If showing backtest results: Label as "hypothetical," disclose assumptions
- [x] No cherry-picked results

**Backtest Disclosure Template** (use if showing results):
```
HYPOTHETICAL PERFORMANCE: Results shown are backtested on historical data. 
These are NOT actual trades. Results may not reflect real-world execution, 
slippage, or costs. Past performance does NOT guarantee future results.
```

---

## 9. State Blue Sky Laws

### ⚠️ Varies by State

**General Approach**:
- Platform provides general information (not state-specific advice)
- No physical presence in user states (cloud-based)
- Likely exempt under "publisher's exclusion"

**Action Items** (if expanding):
- [ ] Review state-specific IA registration requirements
- [ ] Consider nationwide "de minimis" exemption (≤5 clients in state)

---

## 10. Telephone Consumer Protection Act (TCPA)

### ✅ Compliant

- [x] No unsolicited phone calls or SMS
- [x] Email notifications require opt-in (double opt-in for waitlist)
- [x] Clear unsubscribe mechanism (required by CAN-SPAM)

---

## 11. CAN-SPAM Act (Email Marketing)

### ✅ Compliance Measures

- [x] Accurate "From" and "Subject" lines
- [x] Clear identification as advertisement (if promotional)
- [x] Valid physical address in footer
- [x] Unsubscribe link in every email
- [x] Honor opt-outs within 10 business days

---

## 12. GDPR (General Data Protection Regulation) - EU Users

### ✅ Compliance Measures (if serving EU)

- [x] **Lawful Basis**: Consent for service, Legitimate Interest for analytics
- [x] **Data Minimization**: Collect only email + usage data
- [x] **User Rights**: Access, deletion, portability (in Privacy Policy)
- [x] **Data Protection Officer**: Designate if >5000 EU users/month
- [x] **Cookies**: Consent banner for non-essential cookies
- [x] **Data Transfer**: AWS Standard Contractual Clauses (SCC)

---

## 13. CCPA (California Consumer Privacy Act)

### ✅ Compliance (if >$25M revenue OR >50K CA residents)

**Currently Exempt** (MVP stage), but prepared:
- [x] Privacy Policy discloses categories of data collected
- [x] "Do Not Sell My Personal Information" (we don't sell data)
- [x] Right to deletion (process within 45 days)

---

## 14. Accessibility (ADA/Section 508)

### ⚠️ Best Practice (Not Strictly Required for MVP)

- [ ] WCAG 2.1 Level AA compliance for web interface
- [ ] Screen reader compatibility
- [ ] Keyboard navigation

**Recommendation**: Implement for public launch (legal risk mitigation)

---

## 15. Intellectual Property

### ✅ Protections

- [x] **Trademark**: "Political Sentiment Alpha Platform" (consider registration)
- [x] **Copyright**: All content, code, UI (© 2025)
- [x] **Terms of Service**: Prohibit scraping, unauthorized use

---

## 16. Terms of Service (ToS)

### ⚠️ REQUIRED Before Launch

**Must Include**:
- [ ] User obligations (no illegal use, no automated scraping)
- [ ] Limitation of liability
- [ ] Disclaimer of warranties
- [ ] Indemnification clause
- [ ] Governing law & jurisdiction
- [ ] Arbitration clause (recommended)

**Location**: `/terms` endpoint

---

## 17. Disclaimers - Every Page

### ✅ Implemented

- [x] Disclaimer on homepage
- [x] Disclaimer in API responses (`/api/signal` endpoint)
- [x] Disclaimer in email footers
- [x] Standalone disclaimer page (`/disclaimer`)

**Content Requirements**:
- "Not investment advice"
- "Not a registered investment advisor"
- "Past performance ≠ future results"
- "Consult a licensed professional"

---

## 18. Risk Disclosures

### ✅ Comprehensive Disclosure

- [x] Market risk (volatility, loss of capital)
- [x] Model risk (errors, limitations)
- [x] Data risk (delays, inaccuracies)
- [x] Political risk (unforeseen events)
- [x] Execution risk (slippage, liquidity)

**Location**: `templates/disclaimer.html`

---

## 19. Explainability & Transparency

### ✅ Implemented

- [x] Every signal includes explanation (NLP reasoning)
- [x] SHAP-based explainability module (`nlp/explainability.py`)
- [x] Confidence scores displayed prominently
- [x] Methodology documentation (README.md)

**Why**: Compliance with "reasonable basis" for signals (anti-fraud)

---

## 20. Data Security & Breach Notification

### ✅ Measures

- [x] Encryption (TLS 1.2+)
- [x] Access controls (IAM, DB roles)
- [x] Monitoring (CloudWatch, security logs)
- [ ] **Breach Response Plan**: Document 72-hour notification process (GDPR)

**Action Item**:
- [ ] Draft breach notification template (legal counsel review)

---

## 21. Prohibited Conduct

### ✅ Terms of Service Should Prohibit

- [x] Market manipulation (coordination with other users)
- [x] Scraping/unauthorized data collection
- [x] Reverse engineering
- [x] Fraudulent use (fake accounts, referral abuse)

---

## 22. Affiliate/Referral Program Compliance

### ⚠️ FTC Endorsement Guidelines

**If implementing referral rewards**:
- [ ] Clear disclosure of relationship (e.g., "This user will receive credit")
- [ ] No misleading testimonials
- [ ] Referrers must disclose incentive

---

## 23. Pre-Launch Checklist

### Critical Path Items

- [ ] Legal counsel review (30-60 minutes consult, ~$500-$1000)
- [ ] Final disclaimer review
- [ ] Privacy Policy finalized
- [ ] Terms of Service drafted and posted
- [ ] Breach response plan documented
- [ ] Insurance: Errors & Omissions (E&O) policy (recommended)

---

## 24. Ongoing Compliance

### Monthly
- [ ] Review new signals for misleading content
- [ ] Monitor user complaints/feedback

### Quarterly
- [ ] Security audit (access logs, encryption check)
- [ ] Privacy Policy update if needed

### Annually
- [ ] Legal compliance review
- [ ] Update disclaimers for regulatory changes
- [ ] Review insurance coverage

---

## 25. Red Flags to Avoid

### ❌ DO NOT

- Guarantee returns or win rates
- Provide personalized advice ("You should buy X")
- Execute trades on behalf of users
- Collect unnecessary personal data (SSN, portfolio details)
- Share insider information or coordinate trading
- Use testimonials without proper disclosures

---

## Compliance Status Summary

| Area | Status | Priority | Action Required |
|------|--------|----------|----------------|
| Investment Advisor Registration | ✅ Exempt | High | Monitor if add personalized features |
| Privacy Policy | ✅ Complete | High | Posted at `/privacy` |
| Disclaimers | ✅ Complete | Critical | On all pages |
| Terms of Service | ⚠️ Pending | Critical | Draft and post before launch |
| GDPR Compliance | ✅ Ready | Medium | If serving EU users |
| Data Security | ✅ Implemented | High | Regular audits |
| Explainability | ✅ Complete | Medium | Transparency for compliance |

---

**Recommendation**: Schedule 1-hour consultation with securities attorney before public launch (~$500-$1000). Review:
- Disclaimer sufficiency
- Terms of Service
- State registration requirements (if applicable)

---

**Contact**: For compliance questions, email [legal@politicalalpha.com](mailto:legal@politicalalpha.com)

---

© 2025 Political Sentiment Alpha Platform | Compliance Documentation

