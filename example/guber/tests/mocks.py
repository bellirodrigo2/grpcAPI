class MockPaymentGateway:
    async def process_payment(self, payment_data):
        # Mock payment processing
        return {"status": "success", "transaction_id": "mock_tx_123"}


def get_mock_payment_gateway():
    return MockPaymentGateway()
