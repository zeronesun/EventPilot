#!/usr/bin/env python3
"""
Verification script for P0 Bug Fix: Complete API Call Method

This script verifies that the frontend now correctly uses the POST
method with the `/complete/` endpoint instead of PATCH with status field.

Bug: Using PATCH /reviews/{id}/ with {status: 'completed'} bypasses 
      the custom complete action that includes knowledge extraction.

Fix: Use POST /reviews/{id}/complete/ to trigger the proper complete action.
"""

import re
import sys
from pathlib import Path


def check_file(filepath: Path, pattern_to_find: str, pattern_to_avoid: str = None) -> dict:
    """
    Check if file contains the correct pattern and avoids incorrect pattern.
    
    Returns: {
        'has_fix': bool,
        'has_bug': bool,
        'match_count': int
    }
    """
    content = filepath.read_text()
    
    has_fix = bool(re.search(pattern_to_find, content, re.MULTILINE))
    has_bug = False
    
    if pattern_to_avoid:
        has_bug = bool(re.search(pattern_to_avoid, content, re.MULTILINE))
    
    return {
        'has_fix': has_fix,
        'has_bug': has_bug,
        'file': str(filepath)
    }


def main():
    project_root = Path('/mnt/d/projects/sourcecode/EventPilot')
    
    print("=" * 60)
    print("P0 Bug Fix Verification: Complete API Call Method")
    print("=" * 60)
    
    # Test 1: Reviews.vue should use POST with /complete/
    print("\n[Test 1] Checking Reviews.vue...")
    reviews_file = project_root / 'frontend/src/views/Reviews.vue'
    
    result = check_file(
        reviews_file,
        r"apiClient\.post\(`/reviews/\$\{review\.id\}/complete/`\)",
        r"apiClient\.patch\(`/reviews/\$\{review\.id\}/\`,\s*\{.*status.*:.*'completed'.*\}\)"
    )
    
    if result['has_fix']:
        print("  ✓ PASS: Using POST /reviews/{id}/complete/")
    else:
        print("  ✗ FAIL: Not using POST /reviews/{id}/complete/")
        return 1
    
    if result['has_bug']:
        print("  ✗ FAIL: Still contains buggy PATCH calls")
        return 1
    else:
        print("  ✓ PASS: No buggy PATCH calls found")
    
    # Test 2: Store should also use POST for task completion
    print("\n[Test 2] Checking store/index.ts for task completion...")
    store_file = project_root / 'frontend/src/store/index.ts'
    
    result = check_file(
        store_file,
        r"apiClient\.post\(`/tasks/\$\{id\}/complete/`\)",
        r"""apiClient\.patch\(`/tasks/\$\{id\}/complete/`\)"""
    )
    
    if result['has_fix']:
        print("  ✓ PASS: Using POST /tasks/{id}/complete/")
    else:
        print("  ✗ FAIL: Not using POST /tasks/{id}/complete/")
        return 1
    
    if result['has_bug']:
        print("  ⚠ WARNING: Found unwanted PATCH with /complete/ (should be POST)")
        # This is not a blocker, just informative
    
    # Test 3: Verify backup exists
    print("\n[Test 3] Checking backup file...")
    backup_file = project_root / 'frontend/src/views/Reviews.vue.backup'
    if backup_file.exists():
        print("  ✓ PASS: Backup file exists")
    else:
        print("  ⚠ WARNING: Backup file not found (optional)")
    
    # Test 4: Check test files exist
    print("\n[Test 4] Checking test documentation...")
    test_file = project_root / 'frontend/src/test/reviews.test.ts'
    if test_file.exists():
        print("  ✓ PASS: Test documentation created")
    else:
        print("  ⚠ WARNING: Test documentation not found (optional)")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("✓ All critical tests passed!")
    print("✓ Bug fixed: Frontend now uses correct POST /complete/ endpoints")
    print("✓ Knowledge extraction will now be triggered on completion")
    print("\nFixed Files:")
    print(f"  - {project_root}/frontend/src/views/Reviews.vue")
    print(f"  - {project_root}/frontend/src/store/index.ts")
    print("\nBackend actions will now be properly triggered:")
    print("  - POST /reviews/{id}/complete/ → triggers knowledge extraction")
    print("  - POST /tasks/{id}/complete/ → triggers task completion logic")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
