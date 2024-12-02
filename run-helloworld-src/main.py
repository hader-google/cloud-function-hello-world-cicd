# Copyright 2020 Google, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#

def hello_world(request):
    """Example Hello World route."""
    name = os.environ.get("NAME", "World")
    return "Hello {name}!"
