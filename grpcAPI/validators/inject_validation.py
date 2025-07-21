from ctxinject.validate import arg_proc

from grpcAPI.validators import BaseValidator

argproc = arg_proc


class StdValidator(BaseValidator):

    def __init__(
        self,
    ) -> None:
        super().__init__(argproc)
