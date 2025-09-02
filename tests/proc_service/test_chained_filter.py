import pytest

from grpcAPI.service_proc import ChainedFilter, IncludeExclude


class TestChainedFilter:

    def test_init_without_filters(self):
        """Test ChainedFilter initialization without filters"""
        cf = ChainedFilter()
        assert cf.includes_excludes == []
        assert cf.rule_logic == "and"

    def test_init_with_filters(self):
        """Test ChainedFilter initialization with filters"""
        package_filter = IncludeExclude(include=["com.example.*"])
        module_filter = IncludeExclude(exclude=["test*"])

        cf = ChainedFilter(
            includes_excludes=[package_filter, module_filter], rule_logic="or"
        )

        assert len(cf.includes_excludes) == 2
        assert cf.rule_logic == "or"

    def test_empty_filters_includes_everything(self):
        """Test that empty filters include everything"""
        cf = ChainedFilter(includes_excludes=[])

        # Empty filters should return True for any input
        assert cf.should_include([]) is True
        assert cf.should_include(["anything"]) is True

    def test_single_filter_and_logic(self):
        """Test single filter with AND logic"""
        package_filter = IncludeExclude(include=["com.example.*"])
        cf = ChainedFilter(includes_excludes=[package_filter], rule_logic="and")

        # Should match
        assert cf.should_include(["com.example.users"]) is True

        # Should not match
        assert cf.should_include(["com.other.users"]) is False

    def test_multiple_filters_and_logic(self):
        """Test multiple filters with AND logic - all must pass"""
        package_filter = IncludeExclude(include=["com.example.*"])
        module_filter = IncludeExclude(include=["user*"])
        tags_filter = IncludeExclude(include=["api"])

        cf = ChainedFilter(
            includes_excludes=[package_filter, module_filter, tags_filter],
            rule_logic="and",
        )

        # All match - should include
        assert cf.should_include(["com.example.users", "user_service", ["api"]]) is True

        # Package doesn't match - should not include
        assert cf.should_include(["com.other.users", "user_service", ["api"]]) is False

        # Module doesn't match - should not include
        assert (
            cf.should_include(["com.example.users", "admin_service", ["api"]]) is False
        )

        # Tags don't match - should not include
        assert (
            cf.should_include(["com.example.users", "user_service", ["internal"]])
            is False
        )

    def test_multiple_filters_or_logic(self):
        """Test multiple filters with OR logic - any can pass"""
        package_filter = IncludeExclude(include=["com.example.*"])
        module_filter = IncludeExclude(include=["admin*"])
        tags_filter = IncludeExclude(include=["special"])

        cf = ChainedFilter(
            includes_excludes=[package_filter, module_filter, tags_filter],
            rule_logic="or",
        )

        # All match - should include
        assert (
            cf.should_include(["com.example.users", "admin_service", ["special"]])
            is True
        )

        # Only package matches - should include
        assert (
            cf.should_include(["com.example.users", "other_service", ["normal"]])
            is True
        )

        # Only module matches - should include
        assert (
            cf.should_include(["com.other.users", "admin_service", ["normal"]]) is True
        )

        # Only tags match - should include
        assert (
            cf.should_include(["com.other.users", "other_service", ["special"]]) is True
        )

        # Nothing matches - should not include
        assert (
            cf.should_include(["com.other.users", "other_service", ["normal"]]) is False
        )

    def test_hierarchical_logic(self):
        """Test hierarchical logic - package > module > tags precedence"""
        package_filter = IncludeExclude(include=["com.example.*"])
        module_filter = IncludeExclude(include=["user*"])
        tags_filter = IncludeExclude(include=["api"])

        cf = ChainedFilter(
            includes_excludes=[package_filter, module_filter, tags_filter],
            rule_logic="hierarchical",
        )

        # All pass - should include
        assert cf.should_include(["com.example.users", "user_service", ["api"]]) is True

        # Package fails - should not include (stops at package level)
        assert cf.should_include(["com.other.users", "user_service", ["api"]]) is False

        # Package passes, module fails - should not include
        assert (
            cf.should_include(["com.example.users", "admin_service", ["api"]]) is False
        )

        # Package and module pass, tags fail - should not include
        assert (
            cf.should_include(["com.example.users", "user_service", ["internal"]])
            is False
        )

    def test_exclude_filters_with_and_logic(self):
        """Test exclude filters with AND logic"""
        package_filter = IncludeExclude(exclude=["com.test.*"])
        module_filter = IncludeExclude(exclude=["legacy*"])

        cf = ChainedFilter(
            includes_excludes=[package_filter, module_filter], rule_logic="and"
        )

        # Neither excluded - should include
        assert cf.should_include(["com.example.users", "user_service"]) is True

        # Package excluded - should not include
        assert cf.should_include(["com.test.utils", "user_service"]) is False

        # Module excluded - should not include
        assert cf.should_include(["com.example.users", "legacy_service"]) is False

        # Both excluded - should not include
        assert cf.should_include(["com.test.utils", "legacy_service"]) is False

    def test_mixed_include_exclude_filters(self):
        """Test mix of include and exclude filters"""
        package_filter = IncludeExclude(
            include=["com.example.*"], exclude=["com.example.test.*"]
        )
        module_filter = IncludeExclude(include=["user*", "admin*"])
        tags_filter = IncludeExclude(exclude=["deprecated"])

        cf = ChainedFilter(
            includes_excludes=[package_filter, module_filter, tags_filter],
            rule_logic="and",
        )

        # All criteria satisfied - should include
        assert cf.should_include(["com.example.users", "user_service", ["api"]]) is True

        # Package in excluded range - should not include
        assert (
            cf.should_include(["com.example.test.utils", "user_service", ["api"]])
            is False
        )

        # Module not in include list - should not include
        assert (
            cf.should_include(["com.example.users", "payment_service", ["api"]])
            is False
        )

        # Tags contain excluded item - should not include
        assert (
            cf.should_include(
                ["com.example.users", "user_service", ["api", "deprecated"]]
            )
            is False
        )

    def test_tags_as_list_input(self):
        """Test handling of tags as list input"""
        tags_filter = IncludeExclude(include=["api"], exclude=["internal"])

        cf = ChainedFilter(
            includes_excludes=[IncludeExclude(), IncludeExclude(), tags_filter],
            rule_logic="and",
        )

        # Tags list with matching include - should include
        assert (
            cf.should_include(["any.package", "any_module", ["api", "public"]]) is True
        )

        # Tags list with excluded item - should not include
        assert (
            cf.should_include(["any.package", "any_module", ["api", "internal"]])
            is False
        )

        # Tags list without required include - should not include
        assert (
            cf.should_include(["any.package", "any_module", ["public", "util"]])
            is False
        )

    def test_empty_words_list(self):
        """Test behavior with empty words list"""
        cf = ChainedFilter(
            includes_excludes=[IncludeExclude(include=["test"])], rule_logic="and"
        )

        # Empty words list should handle gracefully
        result = cf.should_include([])
        # This depends on implementation - with zip(), it should return True for empty lists
        assert result is True

    def test_mismatched_filter_and_words_count(self):
        """Test behavior when filter count doesn't match words count"""
        package_filter = IncludeExclude(include=["com.example.*"])
        module_filter = IncludeExclude(include=["user*"])

        cf = ChainedFilter(
            includes_excludes=[package_filter, module_filter], rule_logic="and"
        )

        # More words than filters - extra words ignored due to zip()
        result = cf.should_include(["com.example.users", "user_service", "extra_word"])
        assert result is True

        # Fewer words than filters - missing filters ignored due to zip()
        result = cf.should_include(["com.example.users"])
        assert result is True

    @pytest.mark.parametrize("rule_logic", ["and", "or", "hierarchical"])
    def test_rule_logic_options(self, rule_logic: str):
        """Test all supported rule logic options"""
        cf = ChainedFilter(includes_excludes=[IncludeExclude()], rule_logic=rule_logic)
        assert cf.rule_logic == rule_logic

    def test_real_world_service_filtering_scenario(self):
        """Test a realistic service filtering scenario"""
        # Filters matching typical service filtering
        package_filter = IncludeExclude(
            include=["com.myapp.*"], exclude=["com.myapp.test.*", "com.myapp.legacy.*"]
        )
        module_filter = IncludeExclude(exclude=["*_deprecated", "temp*"])
        tags_filter = IncludeExclude(include=["v2"], exclude=["experimental", "alpha"])

        cf = ChainedFilter(
            includes_excludes=[package_filter, module_filter, tags_filter],
            rule_logic="and",
        )

        # Good production service - should include
        assert (
            cf.should_include(["com.myapp.users", "user_service", ["v2", "stable"]])
            is True
        )

        # Test package excluded - should not include
        assert (
            cf.should_include(["com.myapp.test.utils", "test_helper", ["v2"]]) is False
        )

        # Deprecated module excluded - should not include
        assert cf.should_include(["com.myapp.users", "old_deprecated", ["v2"]]) is False

        # Missing v2 tag - should not include
        assert (
            cf.should_include(["com.myapp.users", "user_service", ["v1", "stable"]])
            is False
        )

        # Experimental tag excluded - should not include
        assert (
            cf.should_include(
                ["com.myapp.users", "user_service", ["v2", "experimental"]]
            )
            is False
        )
