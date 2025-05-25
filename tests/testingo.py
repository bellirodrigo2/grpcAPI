# if issubclass(bt, Enum):
#     file = getattr(bt, "protofile", None)
#     pack = getattr(bt, "package", None)
#     prototype = getattr(bt, "prototype", None)
#     qualified = getattr(bt, "qualified_prototype", None)
#     # if callable(file) and callable(pack):
#     #     return None
#     # else:
#     #     return 'Enum type has no callable "protofile" or "package"'
#     if not callable(file) or not callable(pack):
#         return 'Enum type should have callable "protofile" and "package"'
#     elif not callable(prototype) or not callable(qualified):
#         return 'Enum type has no callable "prototype" or "qualified_prototype"'
#     else:
#         return None
