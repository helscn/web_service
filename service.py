# -*- coding: utf-8 -*-

'''

使用 Flask 搭建远程调用代理服务，可以通过路由调用运行服务器上的 Python 模块。

可以将Web请求转发至路由对应的模块的接口函数中，并返回函数运行结果。


转发的路由格式为： /mod/func/route

    mod：需要调用的模块

    func：用于接收请求参数的接口函数，函数接收两个参数：
          第一个位置参数为请求 request 对象；
          第二个位置参数为 route 地址；
          函数返回值将做为请求响应对象返回给客户端。

    route：用于传递给函数的子路由地址，可以省略，此时函数接收的参数为空字符串

当路由中没有指定 *func* 时，模块的文档字符串将做为模块功能介绍返回给客户端。
'''


import os
import sys
from flask import Flask, request, render_template
from importlib import import_module
from traceback import format_exc

sys.path.insert(0, os.path.dirname(__file__))

# Flask 配置
config = {
    "DEBUG": False,                 # 关闭调试模式
    "JSON_AS_ASCII": False          # 避免 JSON 中文乱码
}


app = Flask(__name__)
app.config.from_mapping(config)         # 载入配置字典

MODS_FOLDER = "mods"                      # 指定接口模块的文件夹路径


@app.route('/')
def home(mod=None):
    return render_template(
        'about.html',
        title='About',
        subtitle='服务说明',
        content=__doc__
    )


@app.route('/<mod>/')
def mod(mod):
    try:
        obj = import_module(f'{MODS_FOLDER}.{mod}')
    except:
        return render_template(
            'error.html',
            title='Error',
            subtitle='无法载入指定的模块程序文件',
            mod=mod,
            func='',
            content=format_exc()
        )
    return render_template(
        'mod_info.html',
        title='模块文档',
        subtitle='{0} 模块'.format(mod),
        content=obj.__doc__
    )


@app.route('/<mod>/<func>')
def service(mod, func):
    try:
        obj = import_module(f'{MODS_FOLDER}.{mod}')
    except:
        return render_template(
            'error.html',
            title='Error',
            subtitle='无法载入指定的模块程序文件',
            mod=mod,
            func=func,
            content=format_exc()
        ), 404
    if hasattr(obj, func):
        f = getattr(obj, func)
        if callable(f):
            try:
                return f(request, '')
            except Exception as e:
                return render_template(
                    'error.html',
                    title='Error',
                    subtitle='运行错误',
                    mod=mod,
                    func=func,
                    content=format_exc()
                ), 500
        else:
            return render_template(
                'error.html',
                title='Error',
                subtitle='无法调用接口函数',
                mod=mod,
                func=func,
                content='指定的模块接口函数非可执行对象，请确认函数名是否有误。'
            ), 500
    else:
        return render_template(
            'error.html',
            title='Error',
            subtitle='找不到接口函数',
            mod=mod,
            func=func,
            content='在模块中找不到指定的接口函数，请确认函数名是否有误。'
        ), 404


@app.route('/<mod>/<func>/<path:route>')
def service_with_path(mod, func, route):
    try:
        obj = import_module(f'{MODS_FOLDER}.{mod}')
    except:
        return render_template(
            'error.html',
            title='Error',
            subtitle='无法载入指定的模块程序文件',
            mod=mod,
            func=func,
            route=route,
            content=format_exc()
        ), 404
    if hasattr(obj, func):
        f = getattr(obj, func)
        if callable(f):
            try:
                resp = f(request, route)
                print(resp)
                return resp
            except Exception as e:
                return render_template(
                    'error.html',
                    title='Error',
                    subtitle='运行错误',
                    mod=mod,
                    func=func,
                    route=route,
                    content=format_exc()
                ), 500
        else:
            return render_template(
                'error.html',
                title='Error',
                subtitle='无法调用接口函数',
                mod=mod,
                func=func,
                route=route,
                content='指定的模块接口函数非可执行对象，请确认函数名是否有误。'
            ), 500
    else:
        return render_template(
            'error.html',
            title='Error',
            subtitle='找不到接口函数',
            mod=mod,
            func=func,
            route=route,
            content='在模块中找不到指定的接口函数，请确认函数名是否有误。'
        ), 404


if __name__ == '__main__':
    app.run()
