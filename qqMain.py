import json
import time
import login

from datetime import datetime

# 一天一次
# 失败 6分钟重试一次
# 超过 80次发邮箱
now = datetime.now().day
flag = 0
while True:
    if datetime.now().day != now:
        try:
            r1, r2 = login.Run()
        except Exception as e:
            # 失败写入
            with open("err_qq.out", 'a+')as f:
                f.write("%s\terr:%s\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), e))
            time.sleep(360)
            flag += 1
            if flag == 80:
                # 发送邮件
                login.send_mail()
                # 今天跳过
                now = datetime.now().day
            continue
        now = datetime.now().day
        # 写入成功日志
        with open('success_qq.out', 'a+')as f:
            f.write("%s\t%s\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), json.dumps(r1, ensure_ascii=False)))
            f.write("%s\t%s\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), json.dumps(r2, ensure_ascii=False)))
    time.sleep(1800)
