# -*- coding: utf-8 -*-

'''

Dandanplay 自定义端点服务

可以将此模块地址输入弹弹Play的资源搜索节点地址中，并支持 RSS 输出用于导入下载软件中进行自动下载。
  例如：http://host_name/dandanplay

<p>可以查看弹弹Play<a href="https://support.qq.com/products/104929/faqs/93092" target="_blank">使用说明</a>及<a href="https://github.com/kaedei/dandanplay-libraryindex/blob/master/api/ResourceService.md" target="_blank">节点API规范</a>。</p>

'''


from flask import jsonify, Response
import requests
import arrow
import re
from pyquery import PyQuery as pq
from feedgen.feed import FeedGenerator


proxy_uri = "http://127.0.0.1:7890"
enable_proxy = True


dmhy_base_uri = "https://share.dmhy.org"
dmhy_type_and_subgroup_uri = f"{dmhy_base_uri}/topics/advanced-search?team_id=0&sort_id=0&orderby="
dmhy_list_uri = f"{dmhy_base_uri}/topics/list/page/1?keyword={{0}}&sort_id={{1}}&team_id={{2}}&order=date-desc"
dmhy_rss_uri = f"{dmhy_base_uri}/topics/rss/rss.xml?keyword={{0}}&sort_id={{1}}&&team_id={{2}}&order=date-desc"
unknown_subgroup_id = -1
unknown_subgroup_name = "未知字幕组"

requests.packages.urllib3.disable_warnings()


def get_proxies():
    return {'http': proxy_uri, 'https': proxy_uri} if enable_proxy else None


def convert_size(val):
    result = re.findall(r'(\d+\.?\d*)([T|G|M|K]B)', val)
    if val:
        size = float(result[0][0])
        unit = result[0][1]
        if unit == 'KB':
            return int(size*1024)
        elif unit == 'MB':
            return int(size*1024*1024)
        elif unit == 'GB':
            return int(size*1024*1024*1024)
        elif unit == 'TB':
            return int(size*1024*1024*1024*1024)
    return 1


def parse_rss(tr, feed):
    global dmhy_base_uri
    tds = tr.find('td')

    feed.pubDate(tds.eq(0).find('span').text()+' +0800')
    link0 = tds.eq(1).find('a:first')
    feed.category({
        'term': link0.attr['href'][-1:],
        'scheme': dmhy_base_uri+link0.attr['href'],
        'label': link0.text().strip()
    })
    link1 = tds.eq(2).find('a:last')
    url = dmhy_base_uri+link1.attr['href']
    feed.title(link1.text())
    feed.link(href=url)
    feed.guid(url)

    link2 = tds.eq(3).find('a:first')
    size = convert_size(tds.eq(4).text().strip())
    feed.enclosure(url=link2.attr['href'], length=str(
        size), type='application/x-bittorrent')

    feed.author({'name': tds.eq(8).text().strip()})
    return feed


def parse_list_tr(tr):
    global dmhy_base_uri, unknown_subgroup_id, unknown_subgroup_name
    tds = tr.find('td')
    td1_a0 = tds.eq(1).find('a:first')
    td2_a = tds.eq(2).find('a')
    link = td2_a.eq(-1)
    c1 = len(td2_a)

    return {
        "Title": link.text().strip(),
        "TypeId": int(td1_a0.attr['href'].replace("/topics/list/sort_id/", "")),
        "TypeName": td1_a0.text().strip(),
        "SubgroupId": unknown_subgroup_id if c1 != 2 else int(td2_a.eq(0).attr['href'].replace("/topics/list/team_id/", "")),
        "SubgroupName": unknown_subgroup_name if c1 != 2 else td2_a.eq(0).text().strip(),
        "Magnet": tds.eq(3).find('a:first').attr["href"],
        "PageUrl": dmhy_base_uri + link.attr["href"],
        "FileSize": tds.eq(4).text().strip(),
        "PublishDate": arrow.get(tds.eq(0).find("span:first").text().strip()).format("YYYY-MM-DD HH:mm:ss")
    }


def list(request, route):
    keyword = request.args.get('keyword')
    subgroup = request.args.get('subgroup', 0, type=int)
    type = request.args.get('type', 0, type=int)

    res = requests.get(dmhy_list_uri.format(
        keyword, type, subgroup), proxies=get_proxies(), timeout=8, verify=False)
    res.encoding = "utf-8"
    html = pq(res.text)
    trs = html.find("table#topic_list tbody tr")

    has_more = True if html.find(
        "div.nav_title > a:contains('下一頁')") else False

    return jsonify({"HasMore": has_more, "Resources": [parse_list_tr(tr) for tr in trs.items()]})


def rss(request, route):
    global dmhy_base_uri
    keyword = request.args.get('keyword', '')
    subgroup = request.args.get('subgroup', 0, type=int)
    type = request.args.get('type', 0, type=int)

    res = requests.get(dmhy_list_uri.format(
        keyword, type, subgroup), proxies=get_proxies(), timeout=8, verify=False)
    res.encoding = 'utf-8'
    html = pq(res.text)
    trs = html.find('table#topic_list tbody tr')
    fg = FeedGenerator()
    fg.title(keyword or '动漫花园资源网')
    fg.link(href=dmhy_base_uri)
    fg.language('zh-cn')
    fg.description(
        '动漫花园信息网是一个动漫爱好者交流的平台,提供最及时,最全面的动画,漫画,动漫音乐,动漫下载,BT,ED,动漫游戏,信息,分享,交流,讨论.')

    for tr in trs.items():
        fe = fg.add_entry(order='append')
        parse_rss(tr, fe)

    return Response(fg.rss_str(pretty=True), mimetype='text/xml; charset=utf-8')


def subgroup(request, route):
    global dmhy_type_and_subgroup_uri, unknown_subgroup_id, unknown_subgroup_name
    res = requests.get(dmhy_type_and_subgroup_uri,
                       proxies=get_proxies(), timeout=8, verify=False)
    res.encoding = "utf-8"
    html = pq(res.text)
    options = html.find("select#AdvSearchTeam option")
    subgroups = [{"Id": int(o.val()), "Name": o.text()}
                 for o in options.items()]
    subgroups.append({"Id": unknown_subgroup_id,
                      "Name": unknown_subgroup_name})
    return jsonify({"Subgroups": subgroups})


def type(request, route):
    global dmhy_type_and_subgroup_uri, unknown_subgroup_id, unknown_subgroup_name
    res = requests.get(dmhy_type_and_subgroup_uri,
                       proxies=get_proxies(), timeout=8, verify=False)
    res.encoding = "utf-8"
    html = pq(res.text)
    options = html.find("select#AdvSearchSort option")
    return jsonify({"Types": [{"Id": int(o.val()), "Name": o.text()} for o in options.items()]})
