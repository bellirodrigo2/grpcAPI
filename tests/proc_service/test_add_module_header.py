from dataclasses import dataclass, field
from typing import Any, List, Optional

from grpcAPI.service_proc import IncludeExclude
from grpcAPI.service_proc.add_module_header import (
    AddComment,
    AddLanguageOptions,
    CustomAddOptions,
    MakeOptions,
    make_option,
)


@dataclass
class MockService:
    name: str = "TestService"
    package: str = ""
    module: str = "test_module"
    tags: List[str] = field(default_factory=list)
    active: bool = True
    options: List[str] = field(default_factory=list)
    comments: str = ""
    module_level_options: List[str] = field(default_factory=list)
    module_level_comments: List[str] = field(default_factory=list)

    @property
    def methods(self) -> List[Any]:
        return []

    @property
    def qual_name(self) -> str:
        if self.package:
            return f"{self.package}.{self.name}"
        return self.name


class TestAddComment:

    def test_init_with_comment(self):
        """Test AddComment initialization with basic comment"""
        add_comment = AddComment("// This is a test comment")
        assert add_comment.comment == "// This is a test comment"

    def test_init_strips_whitespace(self):
        """Test that comment whitespace is stripped during initialization"""
        add_comment = AddComment("  // Comment with spaces  \n")
        assert add_comment.comment == "// Comment with spaces"

    def test_init_with_filters(self):
        """Test AddComment initialization with filtering options"""
        package_filter = IncludeExclude(include=["com.example.*"])
        module_filter = IncludeExclude(exclude=["test*"])
        tags_filter = IncludeExclude(include=["api"])

        add_comment = AddComment(
            comment="// API Service",
            package=package_filter,
            module=module_filter,
            tags=tags_filter,
            rule_logic="and",
        )

        assert add_comment.comment == "// API Service"
        assert isinstance(add_comment, AddComment)

    def test_add_comment_to_service(self):
        """Test adding comment to service module_level_options"""
        add_comment = AddComment("// Service comment")
        service = MockService()

        # Initially empty
        assert service.module_level_options == []

        # Add comment
        add_comment._add_comment(service)

        # Comment should be added at the beginning
        assert service.module_level_options == ["// Service comment"]

    def test_add_comment_inserts_at_beginning(self):
        """Test that new comment is inserted at the beginning of options"""
        add_comment = AddComment("// New comment")
        service = MockService(
            module_level_options=["existing option", "another option"]
        )

        add_comment._add_comment(service)

        # New comment should be at index 0
        assert service.module_level_options[0] == "// New comment"
        assert service.module_level_options == [
            "// New comment",
            "existing option",
            "another option",
        ]

    def test_does_not_add_duplicate_comment(self):
        """Test that duplicate comments are not added"""
        add_comment = AddComment("// Duplicate comment")
        service = MockService(
            module_level_options=["// Duplicate comment", "other option"]
        )

        # Try to add the same comment again
        add_comment._add_comment(service)

        # Should not add duplicate
        assert service.module_level_options.count("// Duplicate comment") == 1
        assert service.module_level_options == ["// Duplicate comment", "other option"]

    def test_process_with_matching_filter(self):
        """Test processing service that matches filter criteria"""
        add_comment = AddComment(
            "// Filtered comment",
            package=IncludeExclude(include=["com.example.*"]),
            rule_logic="and",
        )

        # Service matches filter
        matching_service = MockService(package="com.example.users")
        add_comment.process(matching_service)

        # Comment should be added
        assert "// Filtered comment" in matching_service.module_level_options

    def test_process_with_non_matching_filter(self):
        """Test processing service that doesn't match filter criteria"""
        add_comment = AddComment(
            "// Filtered comment",
            package=IncludeExclude(include=["com.example.*"]),
            rule_logic="and",
        )

        # Service doesn't match filter
        non_matching_service = MockService(package="com.other.users")
        add_comment.process(non_matching_service)

        # Comment should NOT be added
        assert "// Filtered comment" not in non_matching_service.module_level_options

    def test_empty_comment_handling(self):
        """Test handling of empty comment"""
        add_comment = AddComment("")
        service = MockService()

        add_comment._add_comment(service)

        # Empty comment should still be added
        assert service.module_level_options == [""]


class TestMakeOptions:

    def test_make_options_protocol(self):
        """Test that MakeOptions protocol works correctly"""

        def option_generator(
            package: Optional[str] = None, module: Optional[str] = None, **kwargs: Any
        ) -> str:
            return f"option(package={package}, module={module})"

        # Should satisfy the protocol
        make_option_func: MakeOptions = option_generator
        result = make_option_func("com.example", "test_module")
        assert result == "option(package=com.example, module=test_module)"


class TestCustomAddOptions:

    def test_init_with_options(self):
        """Test CustomAddOptions initialization with option generators"""

        def option1(package: Optional[str] = None, **kwargs: Any) -> str:
            return f'java_package = "{package}"'

        def option2(
            package: Optional[str] = None, module: Optional[str] = None, **kwargs: Any
        ) -> str:
            return f'java_outer_classname = "{module}Class"'

        add_options = CustomAddOptions([option1, option2])
        assert len(add_options.options) == 2

    def test_add_options_to_service(self):
        """Test adding options to service"""

        def java_package_option(package: Optional[str] = None, **kwargs: Any) -> str:
            return f'java_package = "{package}"'

        def java_class_option(
            package: Optional[str] = None, module: Optional[str] = None, **kwargs: Any
        ) -> str:
            return f'java_outer_classname = "{module}Class"'

        add_options = CustomAddOptions([java_package_option, java_class_option])
        service = MockService(package="com.example.users", module="user_service")

        add_options._add_options(service)

        expected_options = [
            'java_package = "com.example.users"',
            'java_outer_classname = "user_serviceClass"',
        ]
        assert service.module_level_options == expected_options

    def test_add_options_appends_to_existing(self):
        """Test that options are appended to existing module_level_options"""

        def new_option(package: Optional[str] = None, **kwargs: Any) -> str:
            return "new_option = true"

        add_options = CustomAddOptions([new_option])
        service = MockService(
            module_level_options=["existing_option = false"],
            package="com.example",
            module="test",
        )

        add_options._add_options(service)

        assert service.module_level_options == [
            "existing_option = false",
            "new_option = true",
        ]

    def test_does_not_add_duplicate_options(self):
        """Test that duplicate options are not added"""

        def duplicate_option(package: Optional[str] = None, **kwargs: Any) -> str:
            return "duplicate_option = true"

        add_options = CustomAddOptions([duplicate_option])
        service = MockService(
            module_level_options=["duplicate_option = true", "other_option = false"]
        )

        add_options._add_options(service)

        # Should not add duplicate
        assert service.module_level_options.count("duplicate_option = true") == 1
        assert service.module_level_options == [
            "duplicate_option = true",
            "other_option = false",
        ]

    def test_strips_whitespace_from_options(self):
        """Test that whitespace is stripped from generated options"""

        def whitespace_option(package: Optional[str] = None, **kwargs: Any) -> str:
            return "  option_with_spaces = true  \n"

        add_options = CustomAddOptions([whitespace_option])
        service = MockService()

        add_options._add_options(service)

        assert service.module_level_options == ["option_with_spaces = true"]

    def test_skips_empty_options(self):
        """Test that empty options are skipped"""

        def empty_option(package: Optional[str] = None, **kwargs: Any) -> str:
            return ""

        def valid_option(package: Optional[str] = None, **kwargs: Any) -> str:
            return "valid_option = true"

        add_options = CustomAddOptions([empty_option, valid_option])
        service = MockService()

        add_options._add_options(service)

        # Only the valid option should be added
        assert service.module_level_options == ["valid_option = true"]

    def test_process_with_filters(self):
        """Test processing with filtering enabled"""

        def filtered_option(package: Optional[str] = None, **kwargs: Any) -> str:
            return f'filtered_option = "{package}"'

        add_options = CustomAddOptions(
            [filtered_option],
            package=IncludeExclude(include=["com.example.*"]),
            rule_logic="and",
        )

        # Matching service
        matching_service = MockService(package="com.example.users")
        add_options.process(matching_service)
        assert (
            'filtered_option = "com.example.users"'
            in matching_service.module_level_options
        )

        # Non-matching service
        non_matching_service = MockService(package="com.other.users")
        add_options.process(non_matching_service)
        assert len(non_matching_service.module_level_options) == 0


class TestMakeOption:

    def test_make_option_basic_functionality(self):
        """Test basic make_option functionality with simple key-value mapping"""
        kv_map = {
            "java_package": "com.example.{package}",
            "go_package": "github.com/{package}/{module}",
        }

        option_generators = make_option(kv_map)
        option_list = list(option_generators)

        # Should create 2 option generators
        assert len(option_list) == 2

        # Generate all options and check they contain expected values
        results = [
            gen(package="com.myapp.users", module="user_service") for gen in option_list
        ]

        # Should contain both expected options (order may vary)
        assert 'java_package = "com.example.com.myapp.users"' in results
        assert 'go_package = "github.com/com.myapp.users/user_service"' in results

    def test_make_option_with_none_values(self):
        """Test make_option when package or module is None"""
        kv_map = {"java_package": "com.example.{package}.{module}"}

        option_generators = list(make_option(kv_map))
        generator = option_generators[0]

        # Test with None package
        result = generator(None, "test_module")
        assert result == 'java_package = "com.example.{package}.test_module"'

        # Test with None module
        result = generator("com.test", None)
        assert result == 'java_package = "com.example.com.test.{module}"'

        # Test with both None
        result = generator(None, None)
        assert result == 'java_package = "com.example.{package}.{module}"'

    def test_make_option_no_template_variables(self):
        """Test make_option with static values (no template variables)"""
        kv_map = {"java_multiple_files": "true", "optimize_for": "SPEED"}

        option_generators = list(make_option(kv_map))

        # Test static options
        results = [
            gen(package="any.package", module="any_module") for gen in option_generators
        ]

        # Should contain both expected options (order may vary)
        assert 'java_multiple_files = "true"' in results
        assert 'optimize_for = "SPEED"' in results

    def test_make_option_empty_mapping(self):
        """Test make_option with empty mapping"""
        kv_map = {}
        option_generators = list(make_option(kv_map))
        assert len(option_generators) == 0

    def test_make_option_integration_with_custom_add_options(self):
        """Test make_option integration with CustomAddOptions"""
        kv_map = {
            "java_package": "com.generated.{package}",
            "go_package": "github.com/myorg/{module}",
        }

        option_generators = list(make_option(kv_map))
        add_options = CustomAddOptions(option_generators)

        service = MockService(package="com.example.users", module="user_service")
        add_options._add_options(service)

        expected_options = [
            'java_package = "com.generated.com.example.users"',
            'go_package = "github.com/myorg/user_service"',
        ]
        # Check that all expected options are present (order may vary)
        assert len(service.module_level_options) == len(expected_options)
        for expected in expected_options:
            assert expected in service.module_level_options

    def test_complex_template_patterns(self):
        """Test make_option with complex template patterns"""
        kv_map = {
            "complex_option": "{package}.proto.{module}.v1.{package}_service",
            "repeated_package": "{package}-{package}-{module}",
        }

        option_generators = list(make_option(kv_map))

        # Test all generated options
        results = [
            gen(package="com.example", module="user") for gen in option_generators
        ]

        # Should contain both expected options (order may vary)
        assert (
            'complex_option = "com.example.proto.user.v1.com.example_service"'
            in results
        )
        assert 'repeated_package = "com.example-com.example-user"' in results


class TestAddLanguageOptions:

    def test_init_with_simple_mapping(self):
        """Test AddLanguageOptions initialization with simple key-value mapping"""
        kv_map = {
            "java_package": "com.example.{package}",
            "go_package": "github.com/{module}",
        }

        add_lang_options = AddLanguageOptions(language_options={"kv_map": kv_map})
        assert isinstance(add_lang_options, AddLanguageOptions)
        assert isinstance(add_lang_options, CustomAddOptions)

    def test_init_with_filters(self):
        """Test AddLanguageOptions initialization with filtering options"""
        kv_map = {"java_package": "com.example.{package}"}

        add_lang_options = AddLanguageOptions(
            language_options={
                "kv_map": kv_map,
                "package": IncludeExclude(include=["com.myapp.*"]),
                "module": IncludeExclude(exclude=["test*"]),
                "tags": IncludeExclude(include=["api"]),
                "rule_logic": "and",
            }
        )

        assert isinstance(add_lang_options, AddLanguageOptions)

    def test_simple_option_generation(self):
        """Test simple option generation and processing"""
        kv_map = {
            "java_package": "com.generated.{package}",
            "go_package": "github.com/myorg/{module}pb",
        }

        add_lang_options = AddLanguageOptions(language_options={"kv_map": kv_map})
        service = MockService(package="com.example.users", module="user_service")

        add_lang_options.process(service)

        expected_options = [
            'java_package = "com.generated.com.example.users"',
            'go_package = "github.com/myorg/user_servicepb"',
        ]
        # Check that all expected options are present (order may vary)
        assert len(service.module_level_options) == len(expected_options)
        for expected in expected_options:
            assert expected in service.module_level_options

    def test_process_with_filtering(self):
        """Test processing with filtering enabled"""
        kv_map = {"filtered_option": "value_{package}"}

        add_lang_options = AddLanguageOptions(
            language_options={
                "kv_map": kv_map,
                "package": IncludeExclude(include=["com.example.*"]),
                "rule_logic": "and",
            }
        )

        # Matching service - should get options
        matching_service = MockService(package="com.example.users")
        add_lang_options.process(matching_service)
        assert (
            'filtered_option = "value_com.example.users"'
            in matching_service.module_level_options
        )

        # Non-matching service - should not get options
        non_matching_service = MockService(package="com.other.users")
        add_lang_options.process(non_matching_service)
        assert len(non_matching_service.module_level_options) == 0

    def test_empty_mapping(self):
        """Test AddLanguageOptions with empty mapping"""
        kv_map = {}

        add_lang_options = AddLanguageOptions(language_options={"kv_map": kv_map})
        service = MockService()

        add_lang_options.process(service)

        # No options should be added
        assert service.module_level_options == []

    def test_real_world_protobuf_language_options(self):
        """Test realistic multi-language protobuf options"""
        kv_map = {
            "java_package": "com.mycompany.{package}",
            "java_outer_classname": "{module}Proto",
            "java_multiple_files": "true",
            "go_package": "github.com/mycompany/{package}/{module}pb",
            "csharp_namespace": "MyCompany.{package}.{module}",
            "php_namespace": "MyCompany\\{package}\\{module}",
            "ruby_package": "MyCompany::{package}::{module}",
        }

        add_lang_options = AddLanguageOptions(language_options={"kv_map": kv_map})
        service = MockService(package="com.example.users", module="user_service")

        add_lang_options.process(service)

        # Verify all language options are generated (check each individually)
        expected_options = [
            'java_package = "com.mycompany.com.example.users"',
            'java_outer_classname = "user_serviceProto"',
            'java_multiple_files = "true"',
            'go_package = "github.com/mycompany/com.example.users/user_servicepb"',
            'csharp_namespace = "MyCompany.com.example.users.user_service"',
            'php_namespace = "MyCompany\\com.example.users\\user_service"',
            'ruby_package = "MyCompany::com.example.users::user_service"',
        ]

        # Check that all expected options are present
        assert len(service.module_level_options) == len(expected_options)
        for expected in expected_options:
            assert expected in service.module_level_options

    def test_inheritance_behavior(self):
        """Test that AddLanguageOptions properly inherits CustomAddOptions behavior"""
        kv_map = {"test_option": "test_value_{package}"}

        add_lang_options = AddLanguageOptions(language_options={"kv_map": kv_map})
        service = MockService(
            package="com.example", module_level_options=["existing_option = true"]
        )

        add_lang_options.process(service)

        # Should append to existing options (CustomAddOptions behavior)
        assert len(service.module_level_options) == 2
        assert "existing_option = true" in service.module_level_options
        assert 'test_option = "test_value_com.example"' in service.module_level_options

    def test_duplicate_prevention(self):
        """Test that AddLanguageOptions prevents duplicate options"""
        kv_map = {"duplicate_option": "duplicate_value"}

        add_lang_options = AddLanguageOptions(language_options={"kv_map": kv_map})
        service = MockService(
            module_level_options=['duplicate_option = "duplicate_value"']
        )

        add_lang_options.process(service)

        # Should not add duplicate
        assert (
            service.module_level_options.count('duplicate_option = "duplicate_value"')
            == 1
        )

    def test_convenience_over_custom_add_options(self):
        """Test that AddLanguageOptions is more convenient than CustomAddOptions"""
        # With CustomAddOptions, you need to manually call make_option
        kv_map = {"java_package": "com.example.{package}"}
        option_generators = list(make_option(kv_map))
        custom_add_options = CustomAddOptions(option_generators)

        # With AddLanguageOptions, it's more direct
        add_lang_options = AddLanguageOptions(language_options={"kv_map": kv_map})

        # Both should produce the same result
        service1 = MockService(package="com.test")
        service2 = MockService(package="com.test")

        custom_add_options.process(service1)
        add_lang_options.process(service2)

        assert service1.module_level_options == service2.module_level_options
