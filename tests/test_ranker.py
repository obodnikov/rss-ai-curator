"""Basic tests for ArticleRanker."""
import pytest
from datetime import datetime
from src.ranker import ArticleRanker
from src.database import Article


class TestArticleRanker:
    """Test ArticleRanker functionality."""
    
    @pytest.fixture
    def sample_article(self):
        """Create a sample article for testing."""
        return Article(
            id=1,
            url="https://example.com/test",
            title="Test Article about AI",
            content="This is a test article about artificial intelligence.",
            summary="Test article about AI",
            source="Test Source",
            published_at=datetime.utcnow(),
            content_hash="abc123"
        )
    
    def test_parse_response(self):
        """Test LLM response parsing."""
        # This would need proper mocking of the ranker
        # For now, just a placeholder test
        assert True
    
    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        import numpy as np
        from src.ranker import ArticleRanker
        
        vec1 = np.array([1, 0, 0])
        vec2 = np.array([1, 0, 0])
        
        similarity = ArticleRanker._cosine_similarity(vec1, vec2)
        assert similarity == 1.0
        
        vec3 = np.array([0, 1, 0])
        similarity = ArticleRanker._cosine_similarity(vec1, vec3)
        assert similarity == 0.0


# To run tests:
# pytest tests/