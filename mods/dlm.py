# -*- coding: utf-8 -*-

'''

DLM 代理服务

用于Synology Download Station的搜索代理服务
使用 dlm/proxy/实际网站地址 进行代理访问
实际访问域名的路由和 GET 请求参数会自动进行转发查询。
'''


from flask import Response
import requests


proxy_uri = "http://127.0.0.1:7890"
enable_proxy = False


requests.packages.urllib3.disable_warnings()


def get_proxies():
    return {'http': proxy_uri, 'https': proxy_uri} if enable_proxy else None


def proxy(request,url):
    url = "{}?{}".format(url, request.query_string.decode("utf8"))
    res = requests.get(url,proxies=get_proxies(), timeout=8, verify=False)
    content_type=res.headers.get("Content-Type","text/html")
    return Response(res.content,status=res.status_code,content_type=content_type)

