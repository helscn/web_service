# -*- coding: utf-8 -*-

'''

Dandanplay 自定义端点服务

可以将此模块地址输入弹弹Play的资源搜索节点地址中，并支持 RSS 输出用于导入下载软件中进行自动下载。
  例如：http://host_name/dandanplay

<p>可以查看弹弹Play<a href="https://support.qq.com/products/104929/faqs/93092" target="_blank">使用说明</a>及<a href="https://github.com/kaedei/dandanplay-libraryindex/blob/master/api/ResourceService.md" target="_blank">节点API规范</a>。</p>

'''


from flask import jsonify, Response
import requests
from bs4 import BeautifulSoup
import arrow


proxy_uri = "http://127.0.0.1:7890"
enable_proxy = False


dmhy_base_uri = "https://share.dmhy.org"
dmhy_type_and_subgroup_uri = f"{dmhy_base_uri}/topics/advanced-search?team_id=0&sort_id=0&orderby="
dmhy_list_uri = f"{dmhy_base_uri}/topics/list/page/1?keyword={{0}}&sort_id={{1}}&team_id={{2}}&order=date-desc"
dmhy_rss_uri = f"{dmhy_base_uri}/topics/rss/rss.xml?keyword={{0}}&sort_id={{1}}&&team_id={{2}}&order=date-desc"
unknown_subgroup_id = -1
unknown_subgroup_name = "未知字幕组"

requests.packages.urllib3.disable_warnings()


def get_proxies():
    return {'http': proxy_uri, 'https': proxy_uri} if enable_proxy else None


def parse_list_tr(tr):
    td0 = tr.select("td")[0]
    td1 = tr.select("td")[1]
    td2 = tr.select("td")[2]
    td3 = tr.select("td")[3]
    td4 = tr.select("td")[4]
    c1 = len(td2.select("a"))
    td1_a0 = td1.select("a")[0]
    td2_a0 = td2.select("a")[0]
    td2_a_last = td2.select("a")[-1]
    td3_a0 = td3.select("a")[0]

    return {
        "Title": td2_a_last.text.strip(),
        "TypeId": int(td1_a0["href"].replace("/topics/list/sort_id/", "")),
        "TypeName": td1_a0.text.strip(),
        "SubgroupId": unknown_subgroup_id if c1 != 2 else int(td2_a0["href"].replace("/topics/list/team_id/", "")),
        "SubgroupName": unknown_subgroup_name if c1 != 2 else td2_a0.text.strip(),
        "Magnet": td3_a0["href"],
        "PageUrl": dmhy_base_uri + td2_a_last["href"],
        "FileSize": td4.text.strip(),
        "PublishDate": arrow.get(td0.select("span")[0].text.strip()).format("YYYY-MM-DD HH:mm:ss")
    }


def list(request, route):
    keyword = request.args.get('keyword')
    subgroup = request.args.get('subgroup', 0, type=int)
    type = request.args.get('type', 0, type=int)

    res = requests.get(dmhy_list_uri.format(
        keyword, type, subgroup), proxies=get_proxies(), timeout=8, verify=False)
    res.encoding = "utf-8"
    soup = BeautifulSoup(res.text, 'html.parser')
    trs = soup.select("table#topic_list tbody tr")
    has_more = True if soup.select(
        "div.nav_title > a:-soup-contains('下一頁')") else False

    return jsonify({"HasMore": has_more, "Resources": [parse_list_tr(tr) for tr in trs]})


def rss(request, route):
    keyword = request.args.get('keyword')
    subgroup = request.args.get('subgroup', 0, type=int)
    type = request.args.get('type', 0, type=int)

    res = requests.get(dmhy_rss_uri.format(
        keyword, type, subgroup), proxies=get_proxies(), timeout=8, verify=False)
    res.encoding = "utf-8"
    return Response(res.text, mimetype=res.headers['Content-Type'])


def subgroup(request, route):
    res = requests.get(dmhy_type_and_subgroup_uri,
                       proxies=get_proxies(), timeout=8, verify=False)
    res.encoding = "utf-8"
    soup = BeautifulSoup(res.text, 'html.parser')
    options = soup.select("select#AdvSearchTeam option")
    subgroups = [{"Id": int(o["value"]), "Name": o.text} for o in options]
    subgroups.append({"Id": unknown_subgroup_id,
                      "Name": unknown_subgroup_name})
    return jsonify({"Subgroups": subgroups})


def type(request, route):
    res = requests.get(dmhy_type_and_subgroup_uri,
                       proxies=get_proxies(), timeout=8, verify=False)
    res.encoding = "utf-8"
    soup = BeautifulSoup(res.text, 'html.parser')
    options = soup.select("select#AdvSearchSort option")
    return jsonify({"Types": [{"Id": int(o["value"]), "Name": o.text} for o in options]})
