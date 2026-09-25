"""
Semantic Router for Jev
Tests Jev model from OpenRouter using the decisions API
"""

import os
import yaml
import json
from typing import Dict, Any
from dataclasses import dataclass
import httpx
from dotenv import load_dotenv

load_dotenv()


@dataclass
class RoutingDecision:
    model_name: str
    complexity_score: float
    reasoning: str


class SemanticRouter:
    def __init__(self, config_path: str = "semantic_router_config.yaml"):
        """Initialize the semantic router with configuration"""
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")

        self.models = self.config["models"]

    def score_complexity(self, query: str) -> float:
        """Score query complexity on a scale of 1-10"""
        word_count = len(query.split())
        question_marks = query.count("?")
        complexity = min(10, 1 + (word_count / 5) + (question_marks * 2))

        complex_keywords = ["analyze", "compare", "explain", "why", "how", "summarize"]
        if any(keyword in query.lower() for keyword in complex_keywords):
            complexity = min(10, complexity + 2)

        return round(complexity, 1)

    def route(self, query: str) -> RoutingDecision:
        """Route the query - always to Jev"""
        complexity = self.score_complexity(query)
        reasoning = f"Complexity score: {complexity}/10. Routing to Jev."

        return RoutingDecision(
            model_name="jev",
            complexity_score=complexity,
            reasoning=reasoning
        )

    def query_jev_decisions(self, model: str, query: str) -> Dict[str, Any]:
        """Query Jev via OpenRouter decisions API"""
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
        }

        # Convert query into a structured decision task
        payload = {
            "model": model,
            "state": {
                "query": query,
                "context": "User query analysis"
            },
            "questions": {
                "query_type": {
                    "type": "choice",
                    "instructions": "What type of query is this?",
                    "criteria": {
                        "factual": "Asking for facts or information",
                        "analytical": "Asking for analysis or comparison",
                        "creative": "Asking for creative content",
                        "technical": "Asking for technical explanation"
                    }
                },
                "complexity_level": {
                    "type": "score",
                    "instructions": "How complex is this query?",
                    "criteria": [
                        "Simple - Direct answer needed",
                        "Moderate - Some reasoning required",
                        "Complex - Deep analysis needed"
                    ]
                },
                "requires_examples": {
                    "type": "noul",
                    "instructions": "Should the response include examples?",
                    "criteria": {
                        "true": "Query asks for examples or would benefit from them",
                        "false": "Query doesn't require examples"
                    }
                }
            }
        }

        response = httpx.post(
            "https://openrouter.ai/api/alpha/decisions",
            headers=headers,
            json=payload,
            timeout=60.0
        )

        if response.status_code != 200:
            error_detail = response.text
            raise ValueError(f"OpenRouter decisions API error ({response.status_code}): {error_detail}")

        result = response.json()
        return result.get("answers", result)

    def process(self, query: str) -> Dict[str, Any]:
        """Process a query through the semantic router"""
        routing_decision = self.route(query)
        model_config = self.models["jev"]
        model_id = model_config["name"]

        decisions = self.query_jev_decisions(model_id, query)

        return {
            "query": query,
            "routing_decision": {
                "model": routing_decision.model_name,
                "complexity_score": routing_decision.complexity_score,
                "reasoning": routing_decision.reasoning,
            },
            "decisions": decisions,
        }


if __name__ == "__main__":
    router = SemanticRouter()

    # Test queries
    test_queries = [
        "What is the current time?",
        "Analyze the pros and cons of remote work",
        "How does photosynthesis work?",
        "Generate a creative story about AI",
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")

        result = router.process(query)

        print(f"\nRouting Decision:")
        for key, value in result["routing_decision"].items():
            print(f"  {key}: {value}")

        print(f"\nResponse (first 300 chars):")
        print(f"  {result['response'][:300]}...")
