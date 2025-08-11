from grpcAPI.process_service import IncludeExclude

# Test the IncludeExclude logic
ie1 = IncludeExclude(include=["com.test.*"], exclude=[])
print("Include com.test.*, testing 'com.example':", ie1.should_include("com.example"))
print("Include com.test.*, testing 'com.test.service':", ie1.should_include("com.test.service"))

ie2 = IncludeExclude(include=[], exclude=["com.example.*"])
print("Exclude com.example.*, testing 'com.example':", ie2.should_include("com.example"))
print("Exclude com.example.*, testing 'com.other':", ie2.should_include("com.other"))

ie3 = IncludeExclude(include=[], exclude=[])
print("No filters, testing 'anything':", ie3.should_include("anything"))