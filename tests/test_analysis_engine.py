"""
Test the complete analysis pipeline: Manual Export Parser → Analyzer → Results.

This test demonstrates the full workflow for manual export mode.
"""
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parsers.manual_export import ManualExportParser
from src.analysis.analyzer import FollowerAnalyzer
from src.models import User


def test_full_pipeline():
    """Test the complete pipeline from parsing to analysis."""
    print("=" * 60)
    print("Testing Full Analysis Pipeline")
    print("=" * 60)

    # Step 1: Parse Instagram export
    print("\n[1/3] Parsing Instagram export...")
    fixtures_dir = Path(__file__).parent / 'fixtures'
    parser = ManualExportParser()

    try:
        followers, following = parser.parse_export_directory(fixtures_dir)
        print(f"  ✓ Parsed {len(followers)} followers and {len(following)} following")
    except Exception as e:
        print(f"  ✗ Parser failed: {e}")
        return False

    # Step 2: Analyze relationships
    print("\n[2/3] Analyzing follower relationships...")
    analyzer = FollowerAnalyzer()

    try:
        analysis = analyzer.analyze(
            followers=followers,
            following=following,
            target_username="test_user",
            source="manual_export"
        )
        print(f"  ✓ Analysis complete")
    except Exception as e:
        print(f"  ✗ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 3: Display results
    print("\n[3/3] Analysis Results")
    print("=" * 60)

    summary = analysis.get_summary()
    stats = analysis.statistics

    print(f"\n📊 Overview:")
    print(f"   • Total Following:        {summary['total_following']}")
    print(f"   • Total Followers:        {summary['total_followers']}")
    print(f"   • Analysis Date:          {analysis.analysis_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   • Source:                 {analysis.source}")

    print(f"\n📈 Breakdown:")
    print(f"   • Not Following Back:     {summary['not_following_back']} ({stats['not_following_back_percentage']}%)")
    print(f"   • Mutual Followers:       {summary['mutual_followers']} ({stats['mutual_percentage']}%)")
    print(f"   • Fans (follow you only): {summary['fans']} ({stats['fan_percentage']}%)")

    print(f"\n📐 Ratios:")
    print(f"   • Follower/Following:     {stats['follower_following_ratio']}:1")

    # Expected results based on our test fixtures:
    # Followers: follower1, follower2, follower3
    # Following: following1, following2
    # Not following back: following1, following2 (both are in following but not in followers)
    # Mutual: none (no overlap)
    # Fans: follower1, follower2, follower3 (all followers not in following)

    print(f"\n👥 Detailed Lists:")

    if analysis.not_following_back:
        print(f"\nNot Following Back ({len(analysis.not_following_back)}):")
        for user in analysis.not_following_back:
            print(f"   • @{user.username}")
    else:
        print(f"\nNot Following Back: None")

    if analysis.mutual_followers:
        print(f"\nMutual Followers ({len(analysis.mutual_followers)}):")
        for user in analysis.mutual_followers:
            print(f"   • @{user.username}")
    else:
        print(f"\nMutual Followers: None")

    if analysis.fans:
        print(f"\nFans ({len(analysis.fans)}):")
        for user in analysis.fans:
            print(f"   • @{user.username}")
    else:
        print(f"\nFans: None")

    # Validate expected results
    print(f"\n✅ Validation:")
    expected_not_following_back = 2  # following1, following2
    expected_mutual = 0
    expected_fans = 3  # follower1, follower2, follower3

    checks_passed = True

    if len(analysis.not_following_back) != expected_not_following_back:
        print(f"   ✗ Expected {expected_not_following_back} not following back, got {len(analysis.not_following_back)}")
        checks_passed = False
    else:
        print(f"   ✓ Not following back count: {len(analysis.not_following_back)}")

    if len(analysis.mutual_followers) != expected_mutual:
        print(f"   ✗ Expected {expected_mutual} mutual followers, got {len(analysis.mutual_followers)}")
        checks_passed = False
    else:
        print(f"   ✓ Mutual followers count: {len(analysis.mutual_followers)}")

    if len(analysis.fans) != expected_fans:
        print(f"   ✗ Expected {expected_fans} fans, got {len(analysis.fans)}")
        checks_passed = False
    else:
        print(f"   ✓ Fans count: {len(analysis.fans)}")

    if checks_passed:
        print(f"\n✅ All validation checks passed!")
    else:
        print(f"\n❌ Some validation checks failed")

    # Test serialization
    print(f"\n🔄 Testing serialization...")
    try:
        analysis_dict = analysis.to_dict()
        print(f"   ✓ Serialized to dictionary ({len(analysis_dict)} keys)")

        # Could deserialize back if needed
        # analysis_restored = Analysis.from_dict(analysis_dict)
        print(f"   ✓ Serialization works")
    except Exception as e:
        print(f"   ✗ Serialization failed: {e}")
        checks_passed = False

    print("\n" + "=" * 60)
    if checks_passed:
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = test_full_pipeline()
    sys.exit(0 if success else 1)
