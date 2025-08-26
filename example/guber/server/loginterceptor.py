from grpc.aio import ServerInterceptor


class LoggingInterceptor(ServerInterceptor):
    async def intercept_service(self, continuation, handler_call_details):
        print(f"[gRPC] Method: {handler_call_details.method}")
        print(f"[gRPC] Metadata: {handler_call_details.invocation_metadata}")

        return await continuation(handler_call_details)
