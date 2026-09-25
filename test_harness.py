"""
Test Harness for Semantic Router
Tests routing decisions and compares model responses
"""

import json
import time
import os
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
from semantic_router import SemanticRouter

load_dotenv()


class TestHarness:
    def __init__(self):
        """Initialize the test harness"""
        self.router = SemanticRouter()
        self.results = []
        self.start_time = None

    def run_test(self, query: str, test_name: str = None) -> Dict[str, Any]:
        """Run a single test"""
        test_name = test_name or f"test_{len(self.results) + 1}"

        start = time.time()
        try:
            result = self.router.process(query)
            elapsed = time.time() - start

            decisions = result.get("decisions", {})
            decisions_str = json.dumps(decisions, indent=2)[:300]

            test_result = {
                "test_name": test_name,
                "query": query,
                "routing_decision": result["routing_decision"],
                "decisions": decisions,
                "decisions_preview": decisions_str,
                "latency_seconds": round(elapsed, 2),
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
        except Exception as e:
            test_result = {
                "test_name": test_name,
                "query": query,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "failed"
            }

        self.results.append(test_result)
        return test_result

    def run_suite(self, test_queries: List[Dict[str, str]]):
        """Run a suite of tests"""
        self.start_time = time.time()

        for test in test_queries:
            query = test.get("query")
            name = test.get("name", f"test_{len(self.results) + 1}")
            print(f"\n📝 Running: {name}")
            print(f"   Query: {query}")

            result = self.run_test(query, name)

            if result["status"] == "success":
                print(f"   ✅ Model: {result['routing_decision']['model']}")
                print(f"   ⏱️  Latency: {result['latency_seconds']}s")
                print(f"   🧠 Complexity: {result['routing_decision']['complexity_score']}/10")
                print(f"   🎯 Decisions: {json.dumps(result.get('decisions', {}), indent=6)[:150]}...")
            else:
                print(f"   ❌ Error: {result.get('error')}")

    def print_summary(self):
        """Print a summary of test results"""
        total_time = time.time() - self.start_time if self.start_time else 0
        successful = [r for r in self.results if r["status"] == "success"]
        failed = [r for r in self.results if r["status"] == "failed"]

        print(f"\n{'='*60}")
        print(f"TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {len(self.results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        print(f"Total Time: {total_time:.2f}s")

        if successful:
            avg_latency = sum(r["latency_seconds"] for r in successful) / len(successful)
            print(f"Avg Latency: {avg_latency:.2f}s")

        # Model usage breakdown
        if successful:
            model_usage = {}
            for r in successful:
                model = r["routing_decision"]["model"]
                model_usage[model] = model_usage.get(model, 0) + 1

            print(f"\n📊 Model Usage:")
            for model, count in model_usage.items():
                print(f"   {model}: {count} queries")

        # Decision type breakdown
        if successful:
            decision_type_usage = {}
            for r in successful:
                decisions = r.get("decisions", {})
                if "query_type" in decisions:
                    query_type = decisions["query_type"].get("choice", "unknown")
                    decision_type_usage[query_type] = decision_type_usage.get(query_type, 0) + 1

            if decision_type_usage:
                print(f"\n🎯 Query Type Breakdown:")
                for qtype, count in decision_type_usage.items():
                    print(f"   {qtype}: {count} queries")

    def save_results(self, filename: str = None):
        """Save results to JSON file"""
        filename = filename or f"router_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to {filename}")
        return filename

    def compare_models(self):
        """Compare performance across models"""
        if not self.results:
            print("No results to compare")
            return

        model_stats = {}
        for result in self.results:
            if result["status"] == "success":
                model = result["routing_decision"]["model"]
                if model not in model_stats:
                    model_stats[model] = {"count": 0, "total_latency": 0}

                model_stats[model]["count"] += 1
                model_stats[model]["total_latency"] += result["latency_seconds"]

        print(f"\n{'='*60}")
        print(f"MODEL COMPARISON")
        print(f"{'='*60}")

        for model, stats in model_stats.items():
            avg_latency = stats["total_latency"] / stats["count"]
            print(f"\n{model}:")
            print(f"  Queries: {stats['count']}")
            print(f"  Avg Latency: {avg_latency:.2f}s")
            print(f"  Total Latency: {stats['total_latency']:.2f}s")


# Define test queries
DEFAULT_TEST_QUERIES = [
    {
        "name": "simple_status_check",
        "query": "What is the current status of the system?"
    },
    {
        "name": "analysis_task",
        "query": "Analyze the impact of climate change on global trade patterns"
    },
    {
        "name": "complex_reasoning",
        "query": "Compare and contrast machine learning approaches for natural language processing"
    },
    {
        "name": "creative_generation",
        "query": "Write a short story about an AI discovering consciousness"
    },
    {
        "name": "technical_explanation",
        "query": "Explain how transformers work in deep learning"
    },
]


def main():
    print("🚀 Jev Semantic Router Test Harness")
    print("=" * 60)

    # Check for API keys
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY not set")
        print("   Get your key from: https://openrouter.ai/keys")
        return

    # Run tests
    harness = TestHarness()
    harness.run_suite(DEFAULT_TEST_QUERIES)

    # Print results
    harness.print_summary()
    harness.compare_models()

    # Save results
    harness.save_results()


if __name__ == "__main__":
    main()
