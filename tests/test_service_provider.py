# from logging import root

# from grpcAPI.app import BaseService
# from grpcAPI.proto_build import pack_protos


# def test_provide_service_basic(basic_proto: BaseService) -> None:

#     services = {"": [basic_proto]}

#     pack = pack_protos(
#         services=services,
#         root_dir=root,
#     )

#     lib_path = temp_dir / "lib"
#     lib_path.mkdir(parents=True, exist_ok=True)
#     modules_dict = load_proto(
#         root_dir=temp_dir,
#         files=list(pack),
#         dst=lib_path,
#         logger=None,
#         module_factory=GrpcioServiceModule,
#     )
