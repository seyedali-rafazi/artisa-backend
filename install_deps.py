import os
import sys
import urllib.request

urllib.request.getproxies = lambda: {}

for k in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"]:
    os.environ[k] = ""
    os.environ.pop(k, None)

os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"
os.environ["PIP_NO_BUILD_ISOLATION"] = "0"

import pip._internal.cli.main
sys.exit(pip._internal.cli.main.main(["install", "--no-build-isolation", "-r", "requirements.txt"]))
