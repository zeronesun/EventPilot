#!/usr/bin/env python3
"""
Integration test for Reviews complete endpoint with knowledge extraction

This test verifies that the POST /reviews/{id}/complete/ endpoint correctly
triggers knowledge extraction when a review is completed.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import requests
import json
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.reviews.models import Review
from apps.events.models import Event
from apps.knowledge.models import KnowledgeEntry

User = get_user_model()

BASE_URL = "http://localhost:8000/api"


class TestReviewsCompleteEndpoint(TestCase):
    """Test the complete review endpoint"""
    
    def setUp(self):
        """Setup test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='test_review_complete',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test event
        from datetime import datetime, timedelta
        self.event = Event.objects.create(
            name='Test Event for Review Complete',
            type='conference',
            status='executing',
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=1),
            owner=self.user
        )
        
        # Create test review in progress
        self.review = Review.objects.create(
            title='Test Review for Completion',
            event=self.event,
            status='in_progress',
            goal_achievement='Goals were met',
            successes='This is a success story to be extracted',
            improvements='Areas to improve: better planning',
            action_items='Plan better next time',
            created_by=self.user
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_complete_endpoint_extracts_knowledge(self):
        """
        Verify that POST /reviews/{id}/complete/ triggers knowledge extraction
        
        This is the key test to ensure the bug fix is effective:
        - Before fix: PATCH /reviews/{id}/ would update status but NOT extract knowledge
        - After fix: POST /reviews/{id}/complete/ should extract knowledge entries
        """
        # Count knowledge entries before completion
        initial_count = KnowledgeEntry.objects.count()
        
        # Call the complete endpoint (POST, not PATCH)
        response = self.client.post(
            f'/api/reviews/{self.review.id}/complete/'
        )
        
        # Check response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Refresh review from database
        self.review.refresh_from_db()
        
        # Verify review status changed
        assert self.review.status == 'completed', "Review should be completed"
        assert self.review.completed_at is not None, "Review should have completion time"
        
        # Verify knowledge entries were created (this is the key test!)
        final_count = KnowledgeEntry.objects.count()
        
        # Should have created at least 2 entries (successes -> best_practice, improvements -> issue)
        assert final_count >= initial_count + 2, \
            f"Expected knowledge extraction to create entries. Before: {initial_count}, After: {final_count}"
        
        # Verify the content of extracted knowledge
        success_entries = KnowledgeEntry.objects.filter(
            entry_type='best_practice'
        )
        
        
        assert success_entries.exists(), "Success story should be extracted as best_practice"

        issue_entries = KnowledgeEntry.objects.filter(
            entry_type='issue'
        )
        
        assert issue_entries.exists(), "Improvements should be extracted as issue"

        print("✅ Knowledge extraction working correctly!")
        print(f"   - Extracted {final_count - initial_count} knowledge entries")
        print(f"   - Best practices: {success_entries.count()}")
        print(f"   - Issues: {issue_entries.count()}")


def run_manual_test():
    """
    Manual integration test that can run without Django test framework
    """
    print("=" * 60)
    print("Manual Integration Test: Reviews Complete Endpoint")
    print("=" * 60)
    
    # Note: This requires a running backend server
    print("\n⚠️  This test requires a running backend server on localhost:8000")
    print("   Starting with database check...")
    
    try:
        # Try to connect
        r = requests.get(f"{BASE_URL}/reviews/", timeout=2)
        print(f"✅ Backend server is running")
    except requests.exceptions.RequestException:
        print("❌ Backend server not running. Skipping integration test.")
        print("   Run: python manage.py runserver")
        return False
    
    print("\n✅ Integration test would verify:")
    print("   1. POST /reviews/{id}/complete/ endpoint exists and responds")
    print("   2. Review status changes to 'completed'")
    print("   3. completed_at timestamp is set")
    print("   4. Knowledge entries are created (best_practices, issues)")
    print("   5. Frontend now uses POST /complete/ instead of PATCH")
    
    return True


if __name__ == '__main__':
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    # Run as pytest or manually
    try:
        import pytest
        pytest.main([__file__, '-v'])
    except ImportError:
        print("pytest not found, running manual check...")
        run_manual_test()
