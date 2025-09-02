from dataclasses import dataclass, field
from typing import Any, List, Optional

import pytest

from grpcAPI.service_proc.filter_service import DisableService


@dataclass
class MockMethod:
    name: str = "test_method"
    package: str = ""
    module: str = "test_module"
    tags: List[str] = field(default_factory=list)
    active: bool = True
    service: str = "TestService"
    options: List[str] = field(default_factory=list)
    comments: str = ""
    method: Any = field(default=lambda x: x)
    request_types: List[Any] = field(default_factory=list)
    response_types: Optional[Any] = None


@dataclass
class MockService:
    name: str = "TestService"
    package: str = ""
    module: str = "test_module"
    tags: List[str] = field(default_factory=list)
    active: bool = True
    options: List[str] = field(default_factory=list)
    comments: str = ""
    _methods: List[MockMethod] = field(default_factory=list)
    module_level_options: List[str] = field(default_factory=list)
    module_level_comments: List[str] = field(default_factory=list)

    @property
    def methods(self) -> List[MockMethod]:
        return self._methods

    @property
    def qual_name(self) -> str:
        if self.package:
            return f"{self.package}.{self.name}"
        return self.name


class TestDisableService:

    def test_init_without_filter(self):
        """Test DisableService initialization without service_filter"""
        disable_service = DisableService()
        assert isinstance(disable_service, DisableService)

    def test_init_with_service_filter(self):
        """Test DisableService initialization with service_filter"""
        disable_service = DisableService(
            service_filter={
                "package": {"include": ["com.example.*"], "exclude": []},
                "module": {"include": [], "exclude": ["test*"]},
                "tags": {"include": ["api"], "exclude": ["internal"]},
                "rule_logic": "and",
            }
        )
        assert isinstance(disable_service, DisableService)

    def test_disable_method_sets_active_false(self):
        """Test that _disable method sets active to False"""
        disable_service = DisableService()
        mock_service = MockService()
        assert mock_service.active is True

        disable_service._disable(mock_service)
        assert mock_service.active is False

    def test_no_filter_keeps_all_active(self):
        """Test that service without filters keeps everything active"""
        disable_service = DisableService()

        service = MockService(
            name="TestService", package="com.example", module="user_service"
        )
        method = MockMethod(
            name="create_user", package="com.example", module="user_service"
        )
        service._methods = [method]

        disable_service.process(service)

        assert service.active is True
        assert method.active is True

    def test_package_include_filter(self):
        """Test package include filtering"""
        disable_service = DisableService(
            service_filter={
                "package": {"include": ["com.example.*"], "exclude": []},
                "rule_logic": "and",
            }
        )

        # Should remain active - matches include pattern
        matching_service = MockService(package="com.example.users")
        disable_service.process(matching_service)
        assert matching_service.active is True

        # Should be disabled - doesn't match include pattern
        non_matching_service = MockService(package="com.other.users")
        disable_service.process(non_matching_service)
        assert non_matching_service.active is False

    def test_package_exclude_filter(self):
        """Test package exclude filtering"""
        disable_service = DisableService(
            service_filter={
                "package": {"include": [], "exclude": ["com.test.*"]},
                "rule_logic": "and",
            }
        )

        # Should remain active - doesn't match exclude pattern
        good_service = MockService(package="com.example.users")
        disable_service.process(good_service)
        assert good_service.active is True

        # Should be disabled - matches exclude pattern
        excluded_service = MockService(package="com.test.utils")
        disable_service.process(excluded_service)
        assert excluded_service.active is False

    def test_module_filter(self):
        """Test module filtering"""
        disable_service = DisableService(
            service_filter={
                "module": {"include": ["user*"], "exclude": ["admin*"]},
                "rule_logic": "and",
            }
        )

        # Should remain active - matches include, doesn't match exclude
        user_service = MockService(module="user_service")
        disable_service.process(user_service)
        assert user_service.active is True

        # Should be disabled - doesn't match include
        other_service = MockService(module="payment_service")
        disable_service.process(other_service)
        assert other_service.active is False

        # Should be disabled - matches exclude
        admin_service = MockService(module="admin_service")
        disable_service.process(admin_service)
        assert admin_service.active is False

    def test_tags_filter(self):
        """Test tags filtering"""
        disable_service = DisableService(
            service_filter={
                "tags": {"include": ["api"], "exclude": ["internal"]},
                "rule_logic": "and",
            }
        )

        # Should remain active - has api tag, no internal tag
        api_service = MockService(tags=["api", "public"])
        disable_service.process(api_service)
        assert api_service.active is True

        # Should be disabled - no api tag
        no_api_service = MockService(tags=["public", "util"])
        disable_service.process(no_api_service)
        assert no_api_service.active is False

        # Should be disabled - has internal tag (excluded)
        internal_service = MockService(tags=["api", "internal"])
        disable_service.process(internal_service)
        assert internal_service.active is False

    def test_and_rule_logic(self):
        """Test AND rule logic - all criteria must match"""
        disable_service = DisableService(
            service_filter={
                "package": {"include": ["com.example.*"], "exclude": []},
                "module": {"include": ["user*"], "exclude": []},
                "tags": {"include": ["api"], "exclude": []},
                "rule_logic": "and",
            }
        )

        # Should remain active - matches all criteria
        perfect_match = MockService(
            package="com.example.users", module="user_service", tags=["api"]
        )
        disable_service.process(perfect_match)
        assert perfect_match.active is True

        # Should be disabled - doesn't match package
        bad_package = MockService(
            package="com.other.users", module="user_service", tags=["api"]
        )
        disable_service.process(bad_package)
        assert bad_package.active is False

        # Should be disabled - doesn't match module
        bad_module = MockService(
            package="com.example.users", module="admin_service", tags=["api"]
        )
        disable_service.process(bad_module)
        assert bad_module.active is False

        # Should be disabled - doesn't match tags
        bad_tags = MockService(
            package="com.example.users", module="user_service", tags=["internal"]
        )
        disable_service.process(bad_tags)
        assert bad_tags.active is False

    def test_or_rule_logic(self):
        """Test OR rule logic - any criteria can match"""
        disable_service = DisableService(
            service_filter={
                "package": {"include": ["com.example.*"], "exclude": []},
                "module": {"include": ["admin*"], "exclude": []},
                "tags": {"include": ["special"], "exclude": []},
                "rule_logic": "or",
            }
        )

        # Should remain active - matches package criteria
        package_match = MockService(
            package="com.example.users", module="other_service", tags=["normal"]
        )
        disable_service.process(package_match)
        assert package_match.active is True

        # Should remain active - matches module criteria
        module_match = MockService(
            package="com.other.service", module="admin_service", tags=["normal"]
        )
        disable_service.process(module_match)
        assert module_match.active is True

        # Should remain active - matches tags criteria
        tags_match = MockService(
            package="com.other.service", module="other_service", tags=["special"]
        )
        disable_service.process(tags_match)
        assert tags_match.active is True

        # Should be disabled - matches no criteria
        no_match = MockService(
            package="com.other.service", module="other_service", tags=["normal"]
        )
        disable_service.process(no_match)
        assert no_match.active is False

    def test_methods_get_processed_independently(self):
        """Test that methods are processed independently of their service"""
        disable_service = DisableService(
            service_filter={
                "module": {"include": ["user*"], "exclude": []},
                "rule_logic": "and",
            }
        )

        # Create methods with different modules
        user_method = MockMethod(name="create_user", module="user_service")
        admin_method = MockMethod(name="create_admin", module="admin_service")

        # Service has mixed module (should be disabled)
        service = MockService(
            name="MixedService",
            module="mixed_service",
            _methods=[user_method, admin_method],
        )

        disable_service.process(service)

        # Service should be disabled (mixed_service doesn't match user*)
        assert service.active is False

        # user_method should remain active (user_service matches user*)
        assert user_method.active is True

        # admin_method should be disabled (admin_service doesn't match user*)
        assert admin_method.active is False

    def test_complex_real_world_scenario(self):
        """Test complex filtering scenario"""
        disable_service = DisableService(
            service_filter={
                "package": {
                    "include": ["com.myapp.*"],
                    "exclude": ["com.myapp.test.*"],
                },
                "module": {"include": [], "exclude": ["legacy*", "*_deprecated"]},
                "tags": {"include": ["v2"], "exclude": ["experimental"]},
                "rule_logic": "and",
            }
        )

        # Should remain active - good service
        good_service = MockService(
            package="com.myapp.users", module="user_service", tags=["v2", "stable"]
        )
        disable_service.process(good_service)
        assert good_service.active is True

        # Should be disabled - wrong package
        wrong_package = MockService(
            package="com.other.users", module="user_service", tags=["v2"]
        )
        disable_service.process(wrong_package)
        assert wrong_package.active is False

        # Should be disabled - test package (excluded)
        test_service = MockService(
            package="com.myapp.test.utils", module="test_utils", tags=["v2"]
        )
        disable_service.process(test_service)
        assert test_service.active is False

        # Should be disabled - legacy module (excluded)
        legacy_service = MockService(
            package="com.myapp.old", module="legacy_handler", tags=["v2"]
        )
        disable_service.process(legacy_service)
        assert legacy_service.active is False

        # Should be disabled - deprecated module (excluded)
        deprecated_service = MockService(
            package="com.myapp.old", module="old_deprecated", tags=["v2"]
        )
        disable_service.process(deprecated_service)
        assert deprecated_service.active is False

        # Should be disabled - no v2 tag
        old_version = MockService(
            package="com.myapp.users", module="user_service", tags=["v1"]
        )
        disable_service.process(old_version)
        assert old_version.active is False

        # Should be disabled - experimental tag (excluded)
        experimental_service = MockService(
            package="com.myapp.new", module="new_service", tags=["v2", "experimental"]
        )
        disable_service.process(experimental_service)
        assert experimental_service.active is False

    @pytest.mark.parametrize("rule_logic", ["and", "or", "hierarchical"])
    def test_rule_logic_options(self, rule_logic: str):
        """Test that all rule logic options are accepted"""
        disable_service = DisableService(
            service_filter={
                "package": {"include": ["test.*"], "exclude": []},
                "rule_logic": rule_logic,
            }
        )
        assert isinstance(disable_service, DisableService)
