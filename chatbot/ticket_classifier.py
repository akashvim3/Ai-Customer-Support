"""
Advanced Ticket Classifier for AI Customer Support Platform.

- Category classification via:
  * Zero-shot NLI model (facebook/bart-large-mnli)
  * Optional traditional TF‑IDF + RandomForest model
  * Rule-based fallback

- Priority classification via keyword + metadata rules.
"""

import logging
import os
from typing import Dict, List, Tuple, Optional

from django.conf import settings

import joblib
import numpy as np
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier

logger = logging.getLogger(__name__)

class TicketClassifier:
    """
    ML-powered ticket classification using an ensemble of:
    - Zero-shot NLI model (BART‑MNLI) for flexible labels.
    - Optional traditional TF‑IDF + RandomForest.
    - Rule-based heuristics as a safe fallback.
    """

    def __init__(self) -> None:
        # Categories can be overridden from Django settings
        self.categories: List[str] = getattr(
            settings,
            "TICKET_CATEGORIES",
            [
                "Technical Issue",
                "Billing",
                "Account Management",
                "Product Inquiry",
                "Feature Request",
                "Bug Report",
                "General Support",
            ],
        )

        self.models_base = getattr(settings, "ML_MODELS_PATH", "ml_models/saved_models")
        os.makedirs(self.models_base, exist_ok=True)

        self.bert_classifier = None
        self.traditional_model: Optional[RandomForestClassifier] = None
        self.vectorizer: Optional[TfidfVectorizer] = None

        self._setup_bert_classifier()
        self._setup_traditional_classifier()
        self.priority_keywords = self._load_priority_keywords()

    # ------------------------------------------------------------------
    # Model setup
    # ------------------------------------------------------------------
    def _setup_bert_classifier(self) -> None:
        """
        Initialize Hugging Face zero-shot classification pipeline
        with facebook/bart-large-mnli.
        """
        try:
            device = 0 if getattr(settings, "USE_GPU", False) else -1
            self.bert_classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=device,
            )
            logger.info("Zero‑shot BART‑MNLI classifier initialized successfully.")
        except Exception as exc:
            logger.error("Failed to init BART‑MNLI classifier: %s", exc)
            self.bert_classifier = None

    def _setup_traditional_classifier(self) -> None:
        """
        Load traditional TF‑IDF + RandomForest classifier if present,
        otherwise initialize empty model objects (for later training).
        """
        try:
            model_path = os.path.join(self.models_base, "ticket_classifier.joblib")
            vec_path = os.path.join(self.models_base, "tfidf_vectorizer.joblib")

            if os.path.exists(model_path) and os.path.exists(vec_path):
                self.traditional_model = joblib.load(model_path)
                self.vectorizer = joblib.load(vec_path)
                logger.info("Traditional ticket classifier loaded from disk.")
            else:
                self.vectorizer = TfidfVectorizer(
                    max_features=5000,
                    ngram_range=(1, 2),
                    stop_words="english",
                    min_df=2,
                    max_df=0.8,
                )
                self.traditional_model = RandomForestClassifier(
                    n_estimators=120,
                    max_depth=24,
                    random_state=42,
                )
                logger.info("Initialized new TF‑IDF + RandomForest classifier (untrained).")
        except Exception as exc:
            logger.error("Failed to setup traditional classifier: %s", exc)
            self.traditional_model = None
            self.vectorizer = None

    # ------------------------------------------------------------------
    # Priority rule base
    # ------------------------------------------------------------------
    def _load_priority_keywords(self) -> Dict[str, List[str]]:
        """Keyword buckets used for simple priority scoring."""
        return {
            "urgent": [
                "urgent",
                "emergency",
                "critical",
                "immediately",
                "asap",
                "down",
                "not working",
                "broken",
                "crashed",
                "error",
                "can't access",
                "blocked",
                "security breach",
                "data loss",
                "system down",
                "outage",
                "production issue",
            ],
            "high": [
                "important",
                "soon",
                "high priority",
                "affecting multiple",
                "production",
                "customer facing",
                "revenue impact",
                "business critical",
                "major issue",
                "severe",
            ],
            "medium": [
                "need help",
                "issue",
                "problem",
                "question",
                "not sure",
                "confused",
                "clarification",
                "assistance",
                "support needed",
                "help required",
            ],
            "low": [
                "when possible",
                "future",
                "enhancement",
                "suggestion",
                "feedback",
                "nice to have",
                "eventually",
                "minor",
                "cosmetic",
                "improvement",
            ],
        }

    # ------------------------------------------------------------------
    # Public entrypoint
    # ------------------------------------------------------------------
    def classify_ticket(
        self,
        title: str,
        description: str,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Classify a ticket into category + priority and add useful hints.

        Returns dict:
        {
            "category": str,
            "category_confidence": float,
            "priority": str,
            "priority_confidence": float,
            "tags": List[str],
            "estimated_resolution_time": str,
            "suggested_team": str,
            "top_categories": List[{category, confidence}],
            "classification_method": "ensemble" | "bert" | "traditional" | "rules",
        }
        """
        try:
            text = f"{title}. {description}"

            # Category via ensemble
            cat_result = self._classify_category(text)

            # Priority via rules + metadata
            pri_result = self._classify_priority(title, description, metadata or {})

            tags = self._extract_tags(text)
            eta = self._estimate_resolution_time(cat_result["category"], pri_result["priority"])
            team = self._suggest_team(cat_result["category"])

            return {
                "category": cat_result["category"],
                "category_confidence": float(cat_result["confidence"]),
                "priority": pri_result["priority"],
                "priority_confidence": float(pri_result["confidence"]),
                "tags": tags,
                "estimated_resolution_time": eta,
                "suggested_team": team,
                "top_categories": cat_result.get("top_predictions", []),
                "classification_method": cat_result.get("method", "rules"),
            }
        except Exception as exc:
            logger.error("Ticket classification failed: %s", exc)
            return {
                "category": "General Support",
                "category_confidence": 0.5,
                "priority": "medium",
                "priority_confidence": 0.5,
                "tags": [],
                "estimated_resolution_time": "2-3 business days",
                "suggested_team": "general",
                "error": str(exc),
            }

    # ------------------------------------------------------------------
    # Category classification
    # ------------------------------------------------------------------
    def _classify_category(self, text: str) -> Dict:
        """High‑level category classification with ensemble logic."""
        # Try ensemble if both models exist
        if self.bert_classifier and self.traditional_model and self.vectorizer:
            return self._classify_with_ensemble(text)

        # Fall back to the best available model
        if self.bert_classifier:
            return self._classify_with_bert(text)

        if self.traditional_model and self.vectorizer:
            return self._classify_with_traditional(text)

        return self._classify_with_rules(text)

    def _classify_with_bert(self, text: str) -> Dict:
        """Zero-shot classification using BART‑MNLI over dynamic label set."""
        try:
            result = self.bert_classifier(
                text,
                candidate_labels=self.categories,
                multi_label=False,
            )
            labels = result["labels"]
            scores = result["scores"]

            top_label = labels[0]
            top_score = float(scores[0])

            top_predictions = [
                {"category": lbl, "confidence": float(score)}
                for lbl, score in zip(labels[:3], scores[:3])
            ]

            return {
                "category": top_label,
                "confidence": top_score,
                "method": "bert",
                "top_predictions": top_predictions,
            }
        except Exception as exc:
            logger.error("BERT category classification error: %s", exc)
            return self._classify_with_rules(text)

    def _classify_with_traditional(self, text: str) -> Dict:
        """Classify category using TF‑IDF + RandomForest if trained."""
        try:
            X = self.vectorizer.transform([text])
            probs = self.traditional_model.predict_proba(X)[0]
            idx = int(np.argmax(probs))
            label = self.traditional_model.classes_[idx]
            conf = float(probs[idx])

            top_idx = np.argsort(probs)[-3:][::-1]
            top_predictions = [
                {
                    "category": self.traditional_model.classes_[i],
                    "confidence": float(probs[i]),
                }
                for i in top_idx
            ]

            return {
                "category": label,
                "confidence": conf,
                "method": "traditional",
                "top_predictions": top_predictions,
            }
        except Exception as exc:
            logger.error("Traditional category classification error: %s", exc)
            return self._classify_with_rules(text)

    def _classify_with_ensemble(self, text: str) -> Dict:
        """
        Weighted combination of BERT zero‑shot, traditional model,
        and rules for robustness.
        """
        try:
            components = []

            if self.bert_classifier:
                bert = self._classify_with_bert(text)
                components.append(
                    {
                        "category": bert["category"],
                        "confidence": bert["confidence"],
                        "weight": 0.6,
                    }
                )

            if self.traditional_model and self.vectorizer:
                trad = self._classify_with_traditional(text)
                components.append(
                    {
                        "category": trad["category"],
                        "confidence": trad["confidence"],
                        "weight": 0.3,
                    }
                )

            rules = self._classify_with_rules(text)
            components.append(
                {
                    "category": rules["category"],
                    "confidence": rules["confidence"],
                    "weight": 0.1,
                }
            )

            scores: Dict[str, float] = {}
            for comp in components:
                scores[comp["category"]] = scores.get(comp["category"], 0.0) + (
                    comp["confidence"] * comp["weight"]
                )

            sorted_items = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
            final_cat, final_score = sorted_items[0]

            top_predictions = [
                {"category": cat, "confidence": float(score)}
                for cat, score in sorted_items[:3]
            ]

            return {
                "category": final_cat,
                "confidence": float(final_score),
                "method": "ensemble",
                "top_predictions": top_predictions,
            }
        except Exception as exc:
            logger.error("Ensemble category classification error: %s", exc)
            return self._classify_with_rules(text)

    def _classify_with_rules(self, text: str) -> Dict:
        """Simple keyword‑based rules as a safe fallback."""
        text_lower = text.lower()

        keyword_map: Dict[str, List[str]] = {
            "Technical Issue": [
                "error",
                "bug",
                "crash",
                "not working",
                "broken",
                "issue",
                "problem",
                "failed",
                "failure",
                "malfunction",
                "glitch",
                "freeze",
                "hang",
                "slow",
                "timeout",
                "connection",
            ],
            "Billing": [
                "payment",
                "invoice",
                "bill",
                "charge",
                "refund",
                "subscription",
                "pricing",
                "cost",
                "fee",
                "credit card",
                "transaction",
                "receipt",
                "overcharge",
                "discount",
                "upgrade",
            ],
            "Account Management": [
                "account",
                "login",
                "password",
                "access",
                "profile",
                "settings",
                "username",
                "authentication",
                "verification",
                "reset",
                "permissions",
                "two-factor",
                "sign in",
            ],
            "Product Inquiry": [
                "how to",
                "feature",
                "what is",
                "explain",
                "information about",
                "does it",
                "can i",
                "is it possible",
                "functionality",
                "capability",
                "specification",
                "documentation",
            ],
            "Feature Request": [
                "request",
                "add",
                "improve",
                "enhancement",
                "suggestion",
                "would like",
                "wish",
                "hoping",
                "could you add",
                "new feature",
                "implement",
                "integrate",
            ],
            "Bug Report": [
                "bug",
                "error message",
                "wrong",
                "incorrect",
                "unexpected",
                "should",
                "supposed to",
                "reproducible",
                "steps to reproduce",
                "console error",
                "exception",
            ],
            "General Support": [
                "help",
                "support",
                "question",
                "ask",
                "need",
                "assistance",
                "guidance",
                "advice",
                "recommend",
                "best practice",
            ],
        }

        scores: Dict[str, int] = {}
        for cat, kws in keyword_map.items():
            score = 0
            for kw in kws:
                if kw in text_lower:
                    # Slight bonus if kw is a separate token
                    score += 2 if f" {kw} " in f" {text_lower} " else 1
            scores[cat] = score

        if not scores or max(scores.values()) == 0:
            return {
                "category": "General Support",
                "confidence": 0.5,
                "method": "rules",
                "top_predictions": [{"category": "General Support", "confidence": 0.5}],
            }

        total = sum(scores.values())
        best_cat = max(scores, key=scores.get)
        best_score = scores[best_cat] / max(total, 1)

        sorted_scores = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:3]
        top_predictions = [
            {"category": cat, "confidence": float(sc / max(total, 1))}
            for cat, sc in sorted_scores
            if sc > 0
        ]

        return {
            "category": best_cat,
            "confidence": float(best_score),
            "method": "rules",
            "top_predictions": top_predictions or [
                {"category": "General Support", "confidence": 0.5}
            ],
        }

    # ------------------------------------------------------------------
    # Priority classification
    # ------------------------------------------------------------------
    def _classify_priority(
        self,
        title: str,
        description: str,
        metadata: Dict,
    ) -> Dict:
        """Priority based on keywords + optional metadata (tier, SLA, etc.)."""
        text = f"{title} {description}".lower()
        scores = {"urgent": 0, "high": 0, "medium": 0, "low": 0}

        # Keyword scoring
        for pri, kws in self.priority_keywords.items():
            for kw in kws:
                if kw in text:
                    scores[pri] += 2 if kw in title.lower() else 1

        # Metadata adjustments
        if metadata.get("customer_tier") == "vip":
            scores["high"] += 3

        if metadata.get("previous_escalations", 0) > 0:
            scores["high"] += 2

        sla_hours = metadata.get("sla_hours")
        if sla_hours is not None:
            if sla_hours <= 2:
                scores["urgent"] += 3
            elif sla_hours <= 8:
                scores["high"] += 2

        # Final decision
        if max(scores.values()) == 0:
            return {"priority": "medium", "confidence": 0.6, "scores": scores}

        total = sum(scores.values())
        best_pri = max(scores, key=scores.get)
        best_raw = scores[best_pri]
        confidence = min(best_raw / max(total, 1) * 1.5, 1.0)

        return {
            "priority": best_pri,
            "confidence": float(confidence),
            "scores": scores,
        }

    # ------------------------------------------------------------------
    # Tag extraction and helpers
    # ------------------------------------------------------------------
    def _extract_tags(self, text: str) -> List[str]:
        """Rough tag extraction to hint at subsystems / topics."""
        text_lower = text.lower()
        tag_map = {
            "api": ["api", "endpoint", "integration", "webhook", "rest", "graphql"],
            "database": ["database", "sql", "query", "table", "migration"],
            "authentication": ["login", "password", "auth", "token", "oauth"],
            "payment": ["payment", "billing", "charge", "invoice", "stripe", "paypal"],
            "ui": ["interface", "ui", "display", "screen", "button", "layout"],
            "performance": ["slow", "performance", "speed", "latency", "timeout"],
            "security": ["security", "breach", "hack", "vulnerability", "ssl", "encryption"],
            "mobile": ["mobile", "ios", "android", "app", "smartphone"],
            "email": ["email", "smtp", "bounce", "delivery", "notification"],
            "reporting": ["report", "analytics", "dashboard", "chart", "export"],
        }

        tags: List[str] = []
        for tag, kws in tag_map.items():
            if any(kw in text_lower for kw in kws):
                tags.append(tag)

        return tags[:5]

    def _estimate_resolution_time(self, category: str, priority: str) -> str:
        """Simple matrix to generate an ETA label."""
        matrix = {
            ("urgent", "Technical Issue"): "2–4 hours",
            ("urgent", "Billing"): "1–2 hours",
            ("urgent", "Account Management"): "1–2 hours",
            ("high", "Technical Issue"): "4–8 hours",
            ("high", "Billing"): "2–4 hours",
            ("high", "Account Management"): "2–4 hours",
            ("medium", "Technical Issue"): "1–2 business days",
            ("medium", "Billing"): "4–8 hours",
            ("medium", "Account Management"): "4–8 hours",
            ("low", "Technical Issue"): "3–5 business days",
            ("low", "Billing"): "1–2 business days",
            ("low", "Account Management"): "1–2 business days",
        }
        return matrix.get((priority, category), "2–3 business days")

    def _suggest_team(self, category: str) -> str:
        """Map high‑level category to an internal team key."""
        mapping = {
            "Technical Issue": "technical",
            "Bug Report": "technical",
            "Billing": "billing",
            "Account Management": "support",
            "Product Inquiry": "support",
            "Feature Request": "product",
            "General Support": "general",
        }
        return mapping.get(category, "general")

    # ------------------------------------------------------------------
    # Training helper (optional, for offline scripts)
    # ------------------------------------------------------------------
    def train_traditional_model(self, training_data: List[Tuple[str, str]]) -> None:
        """
        Train TF‑IDF + RandomForest on labeled ticket data.

        training_data: list of (text, category)
        """
        try:
            if not training_data or len(training_data) < 20:
                logger.warning("Not enough training data (%d) for traditional model.", len(training_data))
                return

            texts, labels = zip(*training_data)
            X = self.vectorizer.fit_transform(texts)
            self.traditional_model.fit(X, labels)

            # Quick in‑sample accuracy
            preds = self.traditional_model.predict(X)
            acc = (preds == np.array(labels)).mean()
            logger.info("Traditional classifier trained. In‑sample accuracy: %.3f", acc)

            joblib.dump(
                self.traditional_model,
                os.path.join(self.models_base, "ticket_classifier.joblib"),
            )
            joblib.dump(
                self.vectorizer,
                os.path.join(self.models_base, "tfidf_vectorizer.joblib"),
            )
            logger.info("Traditional classifier & vectorizer saved to %s", self.models_base)
        except Exception as exc:
            logger.error("Error training traditional classifier: %s", exc)

    def get_training_data_from_tickets(self, max_samples: int = 1000) -> List[Tuple[str, str]]:
        """
        Pull labeled tickets from DB to use as training data
        (e.g. run from a management command).
        """
        from tickets.models import Ticket  # local import to avoid circulars

        qs = (
            Ticket.objects.exclude(category__isnull=True)
            .exclude(category="")
            .filter(ai_confidence__gte=0.7)
            .order_by("-created_at")[:max_samples]
        )

        data: List[Tuple[str, str]] = []
        for t in qs:
            txt = f"{t.title}. {t.description}"
            data.append((txt, t.category))
        return data

# Singleton instance used across the project
ticket_classifier = TicketClassifier()