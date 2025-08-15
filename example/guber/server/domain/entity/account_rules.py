from uuid import uuid4


def make_account_id()->str:
    return str(uuid4())