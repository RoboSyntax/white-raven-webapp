#!/usr/bin/env python3
"""
White Raven Tales - Semantic Story Search Web Application
Gothic horror story discovery powered by Qdrant Vector DB + Ollama embeddings
"""

import os
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from qdrant_client import QdrantClient
from qdrant_client.http import models
import requests

# ============================================================================
# FLASK APP SETUP
# ============================================================================

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Environment configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
COLLECTION_NAME = "white_raven_tales"

# ============================================================================
# QDRANT STORY SEARCH CLASS
# ============================================================================

class QdrantStorySearch:
    """Semantic story search with Qdrant Vector DB + Ollama embeddings"""

    def __init__(self, qdrant_url=QDRANT_URL, ollama_url=OLLAMA_URL):
        self.qdrant = QdrantClient(url=qdrant_url)
        self.ollama_url = ollama_url
        self.collection = COLLECTION_NAME

    def generate_embedding(self, text):
        """Generate 768-dim embedding via Ollama nomic-embed-text"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text},
                timeout=30
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            print(f"[ERROR] Embedding generation failed: {e}")
            return None

    def semantic_search(self, query, filters=None, limit=10):
        """
        Semantic search with advanced filtering

        Filters:
        - mood: List[str] (e.g., ["psychological", "gothic_decay"])
        - min_quality: int (1-10 quality score)
        - source: str ("reddit", "manual", "curated")
        - min_length/max_length: int (video duration in seconds)
        - themes: List[str] (tags like "mirrors", "isolation", "madness")
        """
        # Generate query embedding
        query_vector = self.generate_embedding(query)
        if not query_vector:
            return []

        # Build Qdrant filter conditions
        filter_conditions = []

        if filters:
            # Mood filter (multiple options OR)
            if filters.get("mood") and len(filters["mood"]) > 0:
                filter_conditions.append(
                    models.FieldCondition(
                        key="mood",
                        match=models.MatchAny(any=filters["mood"])
                    )
                )

            # Quality threshold
            if filters.get("min_quality"):
                filter_conditions.append(
                    models.FieldCondition(
                        key="quality_score",
                        range=models.Range(gte=filters["min_quality"])
                    )
                )

            # Video length range
            if filters.get("min_length") or filters.get("max_length"):
                range_filter = {}
                if filters.get("min_length"):
                    range_filter["gte"] = filters["min_length"]
                if filters.get("max_length"):
                    range_filter["lte"] = filters["max_length"]

                filter_conditions.append(
                    models.FieldCondition(
                        key="length_seconds",
                        range=models.Range(**range_filter)
                    )
                )

            # Source filter
            if filters.get("source"):
                filter_conditions.append(
                    models.FieldCondition(
                        key="source",
                        match=models.MatchValue(value=filters["source"])
                    )
                )

        # Qdrant search
        try:
            results = self.qdrant.search(
                collection_name=self.collection,
                query_vector=query_vector,
                limit=limit,
                query_filter=models.Filter(must=filter_conditions) if filter_conditions else None,
                with_payload=True,
                score_threshold=0.5  # Minimum similarity score
            )

            return [self._format_result(hit) for hit in results]
        except Exception as e:
            print(f"[ERROR] Qdrant search failed: {e}")
            return []

    def _format_result(self, hit):
        """Format Qdrant result for API response"""
        content = hit.payload.get("content", "")
        preview = content[:200] + "..." if len(content) > 200 else content

        return {
            "id": str(hit.id),
            "score": round(hit.score, 3),
            "title": hit.payload.get("title", "Untitled"),
            "content": content,
            "preview": preview,
            "mood": hit.payload.get("mood", "unknown"),
            "themes": hit.payload.get("themes", []),
            "quality_score": hit.payload.get("quality_score", 5),
            "length_seconds": hit.payload.get("length_seconds", 60),
            "source": hit.payload.get("source", "unknown"),
            "created_at": hit.payload.get("created_at"),
            "engagement_score": hit.payload.get("engagement_score", 0.0)
        }

    def random_story(self, min_quality=6):
        """Get random high-quality story"""
        try:
            results, _ = self.qdrant.scroll(
                collection_name=self.collection,
                limit=50,
                with_payload=True,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="quality_score",
                            range=models.Range(gte=min_quality)
                        )
                    ]
                )
            )

            if results:
                return self._format_result(random.choice(results))
            return None
        except Exception as e:
            print(f"[ERROR] Random story failed: {e}")
            return None

    def recent_stories(self, limit=12):
        """Get recently added stories (last 30 days)"""
        try:
            # Calculate date 30 days ago
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()

            results, _ = self.qdrant.scroll(
                collection_name=self.collection,
                limit=limit,
                with_payload=True,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="created_at",
                            range=models.Range(gte=thirty_days_ago)
                        )
                    ]
                )
            )

            return [self._format_result(hit) for hit in results]
        except Exception as e:
            print(f"[ERROR] Recent stories failed: {e}")
            # Fallback: get any stories
            return self.get_any_stories(limit)

    def top_stories(self, limit=12):
        """Get highest quality stories"""
        try:
            results, _ = self.qdrant.scroll(
                collection_name=self.collection,
                limit=limit,
                with_payload=True,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="quality_score",
                            range=models.Range(gte=8)
                        )
                    ]
                )
            )

            return [self._format_result(hit) for hit in results]
        except Exception as e:
            print(f"[ERROR] Top stories failed: {e}")
            return self.get_any_stories(limit)

    def get_any_stories(self, limit=12):
        """Fallback: Get any stories from collection"""
        try:
            results, _ = self.qdrant.scroll(
                collection_name=self.collection,
                limit=limit,
                with_payload=True
            )
            return [self._format_result(hit) for hit in results]
        except Exception as e:
            print(f"[ERROR] Get any stories failed: {e}")
            return []

    def get_story_by_id(self, story_id):
        """Get specific story by ID"""
        try:
            result = self.qdrant.retrieve(
                collection_name=self.collection,
                ids=[story_id],
                with_payload=True
            )

            if result:
                return self._format_result(result[0])
            return None
        except Exception as e:
            print(f"[ERROR] Get story by ID failed: {e}")
            return None

    def get_stats(self):
        """Get database statistics"""
        try:
            collection_info = self.qdrant.get_collection(self.collection)

            # Get sample stories to calculate avg quality
            sample_results, _ = self.qdrant.scroll(
                collection_name=self.collection,
                limit=100,
                with_payload=True
            )

            quality_scores = [
                r.payload.get("quality_score", 5)
                for r in sample_results
                if r.payload.get("quality_score")
            ]

            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 5.0

            # Get unique moods (from sample)
            moods = set()
            for r in sample_results:
                mood = r.payload.get("mood")
                if mood:
                    moods.add(mood)

            return {
                "total_stories": collection_info.points_count,
                "moods_count": len(moods),
                "avg_quality": round(avg_quality, 1),
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"[ERROR] Get stats failed: {e}")
            return {
                "total_stories": 0,
                "moods_count": 0,
                "avg_quality": 0.0,
                "last_updated": datetime.now().isoformat()
            }

    def get_moods(self):
        """Get list of available moods"""
        # Predefined moods from WRT brand guide
        return [
            "psychological",
            "gothic_decay",
            "isolation",
            "conspiracy",
            "madness",
            "ancient_dread",
            "urban_legend",
            "whispers"
        ]


# ============================================================================
# INITIALIZE SEARCH CLIENT
# ============================================================================

search_client = QdrantStorySearch()

# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route("/")
def index():
    """Main Gothic dashboard"""
    return render_template("index.html")


@app.route("/api/stories/search", methods=["POST"])
def api_search_stories():
    """Semantic search with filters"""
    try:
        data = request.json
        query = data.get("query", "").strip()
        filters = data.get("filters", {})
        limit = data.get("limit", 12)

        if not query:
            return jsonify({"error": "Query is required"}), 400

        results = search_client.semantic_search(query, filters, limit)
        return jsonify(results)

    except Exception as e:
        print(f"[ERROR] Search API failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/stories/random")
def api_random_story():
    """Get random high-quality story"""
    try:
        story = search_client.random_story(min_quality=6)
        if story:
            return jsonify(story)
        else:
            return jsonify({"error": "No stories found"}), 404
    except Exception as e:
        print(f"[ERROR] Random story API failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/stories/recent")
def api_recent_stories():
    """Get recently added stories"""
    try:
        stories = search_client.recent_stories(limit=12)
        return jsonify(stories)
    except Exception as e:
        print(f"[ERROR] Recent stories API failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/stories/top")
def api_top_stories():
    """Get highest quality stories"""
    try:
        stories = search_client.top_stories(limit=12)
        return jsonify(stories)
    except Exception as e:
        print(f"[ERROR] Top stories API failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/stories/<story_id>")
def api_get_story(story_id):
    """Get specific story by ID"""
    try:
        story = search_client.get_story_by_id(story_id)
        if story:
            return jsonify(story)
        else:
            return jsonify({"error": "Story not found"}), 404
    except Exception as e:
        print(f"[ERROR] Get story API failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/moods")
def api_get_moods():
    """Get list of available moods"""
    try:
        moods = search_client.get_moods()
        return jsonify(moods)
    except Exception as e:
        print(f"[ERROR] Get moods API failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/stats")
def api_get_stats():
    """Get database statistics"""
    try:
        stats = search_client.get_stats()
        return jsonify(stats)
    except Exception as e:
        print(f"[ERROR] Get stats API failed: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🦇 WHITE RAVEN TALES - GOTHIC STORY SEARCH ENGINE")
    print("="*60)
    print(f"\nQdrant URL: {QDRANT_URL}")
    print(f"Ollama URL: {OLLAMA_URL}")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"\nOpen in browser: http://localhost:5000")
    print("\nPress Ctrl+C to stop\n")

    app.run(host="0.0.0.0", port=5000, debug=True)
