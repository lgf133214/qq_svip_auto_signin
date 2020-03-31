import requests
import execjs
import random
import time
import smtplib
import hashlib
import json

from email.mime.text import MIMEText
from email.header import Header



def get_check_params():
    '''
    :param qqMsg: 传递账号，访问 check url用于获取客户端返回字段
    :return: 将需要登录的参数返回
    '''
    checkUrl = '''https://ssl.ptlogin2.qq.com/check?regmaster=&pt_tea=2&pt_vcode=1&uin=1332145262&appid=8000201&js_ver=20021917&js_type=1&login_sig=&u1=https://vip.qq.com/loginsuccess.html&r=%.17f&pt_uistyle=40''' % (
        random.random())
    response = requests.get(checkUrl)
    paramsList = response.text.replace('ptui_checkVC', '') \
        .replace(')', '') \
        .replace("'", '') \
        .replace("(", '') \
        .split(',')
    if paramsList[0] != "0":
        raise Exception("err\t" + "验证码错误")
    params = {
        'verifycode': paramsList[1],
        'pt_verifysession_v1': paramsList[3],
        'ptdrvs': paramsList[5],
    }
    return params


def get_password(account, password, verifycode):
    '''
    :param account: 传递账号
    :param password: 传递密码
    :param verifycode: 传递服务器返回的验证码
    :return: 将加密后的密码返回
    '''
    with open('password.js', 'r', encoding='utf-8') as f:
        jsCode = f.read()
    p = execjs.compile(jsCode).call('$.Encryption.getEncryption', password, account, verifycode, '')
    return p


def login(sess, params):
    '''
    :param sess: 传递session，因为session中携带cookies
    :param params: 登录所需要的参数
    :return: 返回重定向链接
    '''

    headers = {
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
        'accept': '*/*',
        'referer': 'https://xui.ptlogin2.qq.com/cgi-bin/xlogin?appid=8000201&style=20&s_url=https%3A%2F%2Fvip.qq.com%2Floginsuccess.html&maskOpacity=60&daid=18&target=self',
    }

    url = 'https://ssl.ptlogin2.qq.com/login?u=' + params['Account'] + '&verifycode=' + params['verifycode'] + \
          '&pt_vcode_v1=0&pt_verifysession_v1=' + params['pt_verifysession_v1'] + '&p=' + params['p'] + \
          '&pt_randsalt=2&u1=https://vip.qq.com/loginsuccess.html&ptredirect=0&h=1&t=1&g=1&from_ui=1&ptlang=2052&action=1-0-' + str(
        int(time.time_ns() * 1e-6)) + \
          '&js_ver=20021917&js_type=1&login_sig=&pt_uistyle=40&aid=8000201&daid=18&ptdrvs=' + params['ptdrvs'].replace(
        ' ', '')
    response = sess.get(url, headers=headers)
    # 也可以用正则
    # 没有改原来的
    paramsList = response.text.replace('ptuiCB', '') \
        .replace(')', '') \
        .replace("'", '') \
        .replace("(", '') \
        .split(',')
    if "登录成功！" not in response.text:
        raise Exception("err\t" + "登陆失败")
    return paramsList[2]


def Run():
    qqMsg = {
        'Account': 'qq',  # 此处输入自己的账号
        'Password': 'passwd',  # 此处输入自己的密码
    }
    # 验证码、参数等
    params = get_check_params()
    # 密码
    params['p'] = get_password(qqMsg['Account'], qqMsg['Password'], params['verifycode'])
    params.update(qqMsg)
    # 需要拿到cookie
    sess = requests.session()
    # response 登录成功后返回一个网址，发个请求才能得到skey
    response = login(sess, params)
    sess.get(response)
    skey = sess.cookies.get('skey')

    # g_tk 获取
    gtk = ''
    key = 5381
    a = key << 5
    gtk += str(a)
    for i in skey:
        a = (key << 5) + ord(i)
        gtk += str(a)
        key = ord(i)
    gtk += "tencentQQVIP123443safde&!%^%1282"
    m = hashlib.md5()
    m.update(gtk.encode())
    gtk = m.hexdigest()

    # 请求签到地址
    url1 = "https://iyouxi4.vip.qq.com/ams3.0.php?actid=79968&g_tk=" + gtk
    url2 = "https://iyouxi3.vip.qq.com/ams3.0.php?actid=403490&g_tk=" + gtk

    # 解析json
    u1 = json.loads(sess.get(url1).text)
    u2 = json.loads(sess.get(url2).text)
    # 因为忘了记成功响应长什么样，所以就这样写了，问题不大
    if "成功" not in u1['msg']:
        raise Exception("err ", u1, u2)
    if "成功" not in u2['msg']:
        raise Exception("(u1 success) err in u2:", u2)
    return u1, u2


def send_mail():
    # 发信方的信息：发信邮箱，QQ 邮箱授权码
    from_addr = '邮箱'
    password = '密码'

    # 收信方邮箱
    to_addr = from_addr

    # 发信服务器
    # 自己到对应的官网/百度找
    smtp_server = 'smtp.139.com'

    # 邮箱正文内容，第一个参数为内容，第二个参数为格式(plain 为纯文本)，第三个参数为编码
    msg = MIMEText('签到失败，移步服务器查看', 'plain', 'utf-8')

    # 邮件头信息
    msg['From'] = Header(from_addr)
    msg['To'] = Header(to_addr)
    msg['Subject'] = Header('提示信息')

    # 开启发信服务，这里使用的是加密传输
    server = smtplib.SMTP_SSL(host=smtp_server)
    server.connect(smtp_server, 465)
    # 登录发信邮箱
    server.login(from_addr, password)
    # 发送邮件
    server.sendmail(from_addr, to_addr, msg.as_string())
    # 关闭服务器
    server.quit()

