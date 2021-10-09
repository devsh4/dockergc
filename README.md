# Docker Garbage Collection
This application will prune local docker image versions based on the following conditions & assumptions given below:

## Conditions
1. The image version should be older than the given threshold in minutes **AND**
2. The image version shouldn't be one of the latest 3 versions as we want to preserve history
## Assumptions
1. Don't want to prune a single image that has "n" tags, because technically that's still one version & we want to keep last 3 image versions

2. Don't want to prune an image version that has dependent child images but the application handles that exception gracefully.
    - **Example #1** - Docker API will throw an exception if we try to prune an eligible `python:3` image which is being used my another image called `mypythonapp`
    - **Example #2** - Docker API will throw an exception if we try to prune an eligible untagged intermediate image i.e. `<none:<none>` where some of it's layers are being used by a new version of that image

3. We cannot use `prune()` API method for removing images because it only accepts a filter as argument. Since we are creating a custom filter, `remove()` method is a better choice.