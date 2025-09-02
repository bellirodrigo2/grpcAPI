from typing import List, get_args

import pytest
from google.protobuf import descriptor_pool

from grpcAPI.app import APIService, App
from grpcAPI.service_proc.register_descriptor import RegisterDescriptors

# Import real protobuf classes from tests - these imports ensure the descriptors are loaded


def register_service_descriptors(services: List[APIService]) -> None:
    reg_desc = RegisterDescriptors()
    for service in services:
        reg_desc._process_service(service)
    reg_desc.stop()


@pytest.fixture(autouse=True)
def load_proto_descriptors():
    """Ensure all required protobuf descriptors are loaded into the pool"""
    # Import the protobuf modules to ensure their descriptors are registered

    # The act of importing these modules registers their descriptors
    # with the default descriptor pool
    yield


class TestRegisterDescriptors:
    """Test the RegisterDescriptors class"""

    def test_init(self):
        """Test RegisterDescriptors initialization"""
        register = RegisterDescriptors()
        assert register.fds == {}
        assert register.pool is descriptor_pool.Default()

    def test_is_registered(self):
        """Test checking if a file is registered"""
        register = RegisterDescriptors()

        # Should not be registered initially
        assert not register._is_registered("test_file.proto")

    def test_get_fd_creates_new_descriptor(self):
        """Test _get_fd creates new FileDescriptorProto"""
        register = RegisterDescriptors()
        label = ("test_file.proto", "test.package")

        fd = register._get_fd(label)

        assert fd.name == "test_file.proto"
        assert fd.package == "test.package"
        assert label in register.fds

    def test_get_fd_returns_existing_descriptor(self):
        """Test _get_fd returns existing FileDescriptorProto"""
        register = RegisterDescriptors()
        label = ("test_file.proto", "test.package")

        fd1 = register._get_fd(label)
        fd2 = register._get_fd(label)

        assert fd1 is fd2

    def test_add_service_with_real_service(self, functional_service: APIService):
        """Test adding a real APIService creates proper descriptor"""
        register = RegisterDescriptors()

        register._process_service(functional_service)

        # Check that a file descriptor was created
        expected_label = (f"_{functional_service.module}_", functional_service.package)
        assert expected_label in register.fds

        fd = register.fds[expected_label]
        assert fd.name == f"_{functional_service.module}_"
        assert fd.package == functional_service.package

        # Check that service was added
        assert len(fd.service) == 1
        service_desc = fd.service[0]
        assert service_desc.name == functional_service.name

        # Check that methods were added
        assert len(service_desc.method) == len(functional_service.methods)

        # Verify at least one method
        if service_desc.method:
            method_desc = service_desc.method[0]
            original_method = functional_service.methods[0]
            assert method_desc.name == original_method.name
            # Now we use fully qualified names with leading dot
            if original_method.is_client_stream:
                input_type = get_args(original_method.input_type)[0]
            else:
                input_type = original_method.input_type
            if original_method.is_server_stream:
                output_type = get_args(original_method.output_type)[0]
            else:
                output_type = original_method.output_type

            expected_input = f".{input_type.DESCRIPTOR.full_name}"
            expected_output = f".{output_type.DESCRIPTOR.full_name}"
            assert method_desc.input_type == expected_input
            assert method_desc.output_type == expected_output


class TestReflectionIntegration:
    """Integration tests using real gRPC reflection"""

    def test_reflection_with_real_service(self, functional_service: APIService):
        """Test that registered services are discoverable via reflection"""
        register = RegisterDescriptors()

        # Register the real service
        register._process_service(functional_service)
        register.stop()

        # Test that we can find the registered service
        filename = f"_{functional_service.module}_"
        try:
            file_desc = register.pool.FindFileByName(filename)

            # Verify service details
            assert len(file_desc.services_by_name) == 1
            service_desc = file_desc.services_by_name[functional_service.name]
            assert service_desc.name == functional_service.name
            assert service_desc.full_name == functional_service.qual_name

            # Verify method details
            assert len(service_desc.methods) == len(functional_service.methods)

            if service_desc.methods:
                method_desc = service_desc.methods[0]
                original_method = functional_service.methods[0]
                assert method_desc.name == original_method.name
                # Note: input_type and output_type are message descriptors, not names
                assert (
                    method_desc.input_type.name == original_method.input_type.__name__
                )
                assert (
                    method_desc.output_type.name == original_method.output_type.__name__
                )

        except KeyError as e:
            pytest.fail(f"Service not found in descriptor pool: {e}")

    def test_service_names_discoverable(self, functional_service: APIService):
        """Test that service names can be discovered through reflection"""
        register = RegisterDescriptors()

        register._process_service(functional_service)
        register.stop()

        # Get all services from the pool
        discovered_services = []

        # Find all file descriptors in the pool using the public API
        filename = f"_{functional_service.module}_"
        try:
            file_desc = register.pool.FindFileByName(filename)
            if hasattr(file_desc, "services_by_name"):
                for service_name, service_desc in file_desc.services_by_name.items():
                    discovered_services.append(service_desc.full_name)
        except KeyError:
            pass  # File not found

        # Should find our registered service
        expected_full_name = functional_service.qual_name
        assert expected_full_name in discovered_services

    def test_method_signatures_accessible(self, functional_service: APIService):
        """Test that method signatures are properly accessible"""
        register = RegisterDescriptors()
        register._process_service(functional_service)
        register.stop()

        filename = f"_{functional_service.module}_"
        file_desc = register.pool.FindFileByName(filename)
        service_desc = file_desc.services_by_name[functional_service.name]

        # Check that we have methods
        assert len(service_desc.methods) > 0

        method_desc = service_desc.methods[0]
        original_method = functional_service.methods[0]

        # Verify method signature details
        assert method_desc.name == original_method.name
        # Method descriptors have input/output_type as message descriptors, not strings
        if original_method.is_client_stream:
            input_type = get_args(original_method.input_type)[0]
        else:
            input_type = original_method.input_type
        if original_method.is_server_stream:
            output_type = get_args(original_method.output_type)[0]
        else:
            output_type = original_method.output_type

        assert method_desc.input_type.name == input_type.__name__
        assert method_desc.output_type.name == output_type.__name__
        assert method_desc.client_streaming == original_method.is_client_stream
        assert method_desc.server_streaming == original_method.is_server_stream

    def test_duplicate_registration_handled(self, functional_service: APIService):
        """Test that duplicate registrations are handled gracefully"""
        register = RegisterDescriptors()

        # Register same service twice
        register._process_service(functional_service)
        register.stop()

        # Try to register again - should not raise error
        register._process_service(functional_service)
        register.stop()

        # Should still be registered
        filename = f"_{functional_service.module}_"
        assert register._is_registered(filename)


class TestRealWorldScenario:
    """Test realistic scenarios with actual APIService"""

    def test_with_app_services(self, app_fixture: App):
        """Test with real APIService from the framework"""
        register = RegisterDescriptors()

        # Get real services from the app
        if app_fixture.service_list:
            real_service = app_fixture.service_list[0]

            register._process_service(real_service)
            register.stop()

            # Should be able to find it
            expected_filename = f"_{real_service.module}_"
            assert register._is_registered(expected_filename)

            # Should be able to access service details
            file_desc = register.pool.FindFileByName(expected_filename)
            assert len(file_desc.services_by_name) >= 1

            service_desc = file_desc.services_by_name[real_service.name]
            assert service_desc.name == real_service.name
            assert service_desc.full_name == real_service.qual_name

            # Should have methods
            assert len(service_desc.methods) > 0

            for method_desc in service_desc.methods:
                assert method_desc.name
                assert method_desc.input_type
                assert method_desc.output_type

    def test_register_service_descriptors_convenience_function(self, app_fixture: App):
        """Test the convenience function register_service_descriptors"""
        if not app_fixture.service_list:
            pytest.skip("No services in app_fixture")

        # Use the convenience function
        register_service_descriptors(app_fixture.service_list)

        # Create a new register instance to check if services are in the global pool
        register = RegisterDescriptors()

        # Verify all services were registered
        for service in app_fixture.service_list:
            expected_filename = f"_{service.module}_"
            assert register._is_registered(expected_filename)

            # Verify we can access the service
            file_desc = register.pool.FindFileByName(expected_filename)
            assert service.name in file_desc.services_by_name

            service_desc = file_desc.services_by_name[service.name]
            assert service_desc.full_name == service.qual_name

    def test_multiple_services_registration(self, app_fixture: App):
        """Test registering multiple services at once"""
        if len(app_fixture.service_list) < 2:

            # Add a simple method (we can't easily create methods without going through the framework)
            # So we'll just test with the existing service
            register_service_descriptors([app_fixture.service_list[0]])

            register = RegisterDescriptors()
            filename = f"_{app_fixture.service_list[0].module}_"
            assert register._is_registered(filename)
        else:
            # Test with multiple real services
            register_service_descriptors(app_fixture.service_list)

            register = RegisterDescriptors()
            for service in app_fixture.service_list:
                filename = f"_{service.module}_"
                assert register._is_registered(filename)
