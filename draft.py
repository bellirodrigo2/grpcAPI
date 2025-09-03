from ctxinject import DependsInject, ModelFieldInject, Validation


def custom_validator(word: str) -> str:
    if not word.isalpha():
        raise ValueError("Invalid input: only alphabetic characters are allowed.")
    return word.upper()


def func(
    name: str = Validation(min_length=2, pattern=r"^[a-zA-Z]+$"),
    lastname: str = Validation(validator=custom_validator),
    array: Iterable[str] = ModelFieldInject(MyClass, min_length=2, max_length=100),
    db_str: str = DependsInject(get_db, max_length=256),
):
    pass


class MyModel(BaseModel):
    name: str
    age: int


class BaseClass:
    def __init__(self, model: MyModel):
        self.model = model


def handler(
    mymodel: MyModel = CastType(str), model: MyModel = ModelFieldInject(BaseClass)
): ...


mymodel = MyModel(name="John", age=30)
ctx = {mymodel: mymodel, BaseClass: BaseClass(mymodel)}
