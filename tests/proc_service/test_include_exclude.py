import pytest

from grpcAPI.process_service import IncludeExclude


class TestIncludeExclude:

    def test_empty_rules_includes_everything(self) -> None:
        """Test that empty include/exclude rules include everything"""
        ie = IncludeExclude()
        assert ie.should_include("anything") is True
        assert ie.should_include("com.example") is True
        assert ie.should_include(["tag1", "tag2"]) is True

    def test_include_rules_only(self) -> None:
        """Test include rules without exclude rules"""
        ie = IncludeExclude(include=["user*", "admin"])

        # Should include - matches patterns
        assert ie.should_include("user_service") is True
        assert ie.should_include("users") is True
        assert ie.should_include("admin") is True

        # Should not include - doesn't match any pattern
        assert ie.should_include("other_service") is False
        assert ie.should_include("test") is False

    def test_include_rules_with_wildcards(self) -> None:
        """Test include rules with wildcard patterns"""
        ie = IncludeExclude(include=["com.example.*", "*.service"])

        # Should include - matches patterns
        assert ie.should_include("com.example.users") is True
        assert ie.should_include("com.example.admin") is True
        assert ie.should_include("user.service") is True
        assert ie.should_include("admin.service") is True

        # Should not include - doesn't match patterns
        assert ie.should_include("com.other.users") is False
        assert ie.should_include("com.example") is False  # doesn't match com.example.*
        assert ie.should_include("service") is False  # doesn't match *.service

    def test_exclude_rules_only(self) -> None:
        """Test exclude rules without include rules"""
        ie = IncludeExclude(exclude=["test*", "internal"])

        # Should include - doesn't match exclude patterns
        assert ie.should_include("user_service") is True
        assert ie.should_include("admin") is True
        assert ie.should_include("production") is True

        # Should not include - matches exclude patterns
        assert ie.should_include("test_service") is False
        assert ie.should_include("testing") is False
        assert ie.should_include("internal") is False

    def test_include_and_exclude_rules(self) -> None:
        """Test both include and exclude rules together"""
        ie = IncludeExclude(include=["api*"], exclude=["*_internal"])

        # Should include - matches include and doesn't match exclude
        assert ie.should_include("api_service") is True
        assert ie.should_include("api_handler") is True

        # Should not include - doesn't match include
        assert ie.should_include("user_service") is False
        assert ie.should_include("admin") is False

        # Should not include - matches include but also matches exclude
        assert ie.should_include("api_internal") is False

    def test_list_of_names_any_match_include(self) -> None:
        """Test that if any name in list matches include, it should include"""
        ie = IncludeExclude(include=["api"])

        # Should include - one tag matches
        assert ie.should_include(["api", "internal"]) is True
        assert ie.should_include(["user", "api"]) is True

        # Should not include - no tags match
        assert ie.should_include(["user", "internal"]) is False

    def test_list_of_names_any_match_exclude(self) -> None:
        """Test that if any name in list matches exclude, it should exclude"""
        ie = IncludeExclude(exclude=["internal"])

        # Should include - no tags match exclude
        assert ie.should_include(["api", "public"]) is True
        assert ie.should_include(["user"]) is True

        # Should not include - one tag matches exclude
        assert ie.should_include(["api", "internal"]) is False
        assert ie.should_include(["internal", "public"]) is False

    def test_complex_scenario(self) -> None:
        """Test complex include/exclude scenario"""
        ie = IncludeExclude(
            include=["com.example.*", "*.api"], exclude=["*.test.*", "*_internal"]
        )

        # Should include - matches include, doesn't match exclude
        assert ie.should_include("com.example.users") is True
        assert ie.should_include("users.api") is True

        # Should not include - doesn't match include
        assert ie.should_include("com.other.users") is False
        assert ie.should_include("users.service") is False

        # Should not include - matches include but also matches exclude
        assert ie.should_include("com.example.test.utils") is False
        assert ie.should_include("user_internal") is False

    def test_list_vs_string_consistency(self) -> None:
        """Test that single string and list with one item behave the same"""
        ie = IncludeExclude(include=["user*"], exclude=["*_test"])

        # String vs list should give same results
        assert ie.should_include("user_service") == ie.should_include(["user_service"])
        assert ie.should_include("admin") == ie.should_include(["admin"])
        assert ie.should_include("user_test") == ie.should_include(["user_test"])
