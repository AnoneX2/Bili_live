import requests
import json
import time
import qrcode
import os
from apscheduler.schedulers.blocking import BlockingScheduler

black_list=[] #不需要打卡的直播间号列表 用","分割
share_list=[] #需要分享直播间的直播间号列表 用","分割 请勿多于24个


def Get_qrcode():
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'}
    url = 'https://passport.bilibili.com/qrcode/getLoginUrl'  
    res = requests.get(url = url ,headers = headers).json()  #请求登录二维码
    url2 = res['data']['url']
    res2 = requests.get(url = url2).url  #返回跳转后的url地址
    qr = qrcode.QRCode()
    qr.add_data(res2)    #将返回的url地址转换成二维码形式
    # qr.print_ascii(invert=True)
    img = qr.make_image()
    img.show()
    return res['data']['oauthKey']

def Get_cookies(flag='0'):
    while flag!='1' and flag!= '2' :
        flag = input("输入1扫码登录,输入2使用本地token")
    if flag == '1':
        session = requests.session()
        oauthKey = Get_qrcode()
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'}
        url = 'https://passport.bilibili.com/qrcode/getLoginInfo'  
        data = {
            'oauthKey':oauthKey
        }
        time.sleep(10)
        while True:
            res = session.post(url = url,headers = headers ,data = data).json()
            if res['status'] == False:
                print(res['message'])
                time.sleep(10)
            else:
                print('账号登录成功')
                break
        cookies = session.cookies
        cookies_dic = requests.utils.dict_from_cookiejar(cookies)
        with open ('login/cookies.json','w',encoding='utf-8') as f:
            json.dump(cookies_dic,f,ensure_ascii=False)
    if flag == '2':
        try:
            with open ('login/cookies.json','r',encoding='utf-8') as f:
                cookies_dic = json.load(f)
        except:
            print("未找到本地token,请扫码登录")
            session = requests.session()
            oauthKey = Get_qrcode()
            headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'}
            url = 'https://passport.bilibili.com/qrcode/getLoginInfo'  
            data = {
                'oauthKey':oauthKey
            }
            time.sleep(10)
            while True:
                res = session.post(url = url,headers = headers ,data = data).json()
                if res['status'] == False:
                    print(res['message'])
                    time.sleep(10)
                else:
                    print('账号登录成功')
                    break
            cookies = session.cookies
            cookies_dic = requests.utils.dict_from_cookiejar(cookies)
            with open ('login/cookies.json','w',encoding='utf-8') as f:
                json.dump(cookies_dic,f,ensure_ascii=False)
    return cookies_dic

def joint_cookies_dic(cookies_dic):
    cookie = ''
    for name, value in cookies_dic.items():
        cookie += '{0}={1};'.format(name, value)
    return cookie

def get_real_roomid(rid):
    try:
        room_id = int(rid)
        url = f'https://api.live.bilibili.com/xlive/web-room/v1/index/getInfoByRoom?room_id={rid}'
        res = requests.get(url)
        res = res.json()
        room_id = res['data']['room_info']['room_id']
        return room_id
    except:
        print('请输入正确的直播间号')
        return 1

def login_check(cookie):
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
        'cookie': cookie
    }
    url = 'https://api.bilibili.com/x/web-interface/nav'
    res = requests.get(url=url,headers= headers).json()
    if res['data']['isLogin'] ==True:
        name = res['data']['uname']
        print('登录成功,当前账号用户名为%s'%name)
        return 1
    else:
        print('登陆失败,请重新登录')
        return 0


class Login_web(object):
    def __init__(self):
        if not os.path.isdir('login'):
            os.makedirs('login')
        self.black_list=[]
        self.share_list=share_list
        self.cookies_dic = Get_cookies()
        self.cookies = joint_cookies_dic(self.cookies_dic)
        if black_list != []:
            print("正在处理,请稍等...")
            for i in black_list:
                self.black_list.append(get_real_roomid(i))
                time.sleep(2)
        self.check = login_check(self.cookies)
        while self.check!=1:
            self.cookies_dic = Get_cookies(flag='1')
            self.cookies = joint_cookies_dic(self.cookies_dic)
            self.check = login_check(self.cookies)
    
    def get_medal_list(self):
        url = 'https://api.live.bilibili.com/xlive/app-ucenter/v1/fansMedal/panel?page=1&page_size=2000'
        headers = {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
                    'origin': 'https://www.bilibili.com',
                    'sec-fetch-site': 'same-site',
                    'cookie': self.cookies
                }
        res = requests.get(url=url,headers=headers).json()
        medal_list= []
        for i in res['data']['list']:
            medal_list.append(i['room_info']['room_id'])
        medal_list.append(res['data']['special_list'][0]['room_info']['room_id'])
        return medal_list

    def like(self,roomid):
        csrf = self.cookies_dic['bili_jct']
        headers = {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
                    'origin': 'https://www.bilibili.com',
                    'sec-fetch-site': 'same-site',
                    'cookie': self.cookies
                }
        url ='https://api.live.bilibili.com/xlive/web-ucenter/v1/interact/likeInteract'
        data = {
            'roomid':roomid,
            'csrf':csrf,
        }
        res = requests.post(url=url,data=data,headers=headers).json()
        return res

    def send_msg(self,roomid,msg):
        csrf = self.cookies_dic['bili_jct']
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
            'cookie': self.cookies            
            }
        url = 'https://api.live.bilibili.com/msg/send'
        data = {
            'bubble':0,
            'msg':msg,
            'color':16777215,
            'mode':2,
            'fontsize':25,
            'rnd':time.time(),
            'roomid':roomid,
            'csrf':csrf,
            'csrf_token':csrf
            }
        res = requests.post(url=url, data= data ,headers= headers).json()
        if res['message'] != '':
            print('在%s直播间发送"%s"失败'%(roomid,msg))
            return None
        return res

    def share(self,roomid):
        csrf = self.cookies_dic['bili_jct']
        url1 = 'https://api.live.bilibili.com/xlive/app-room/v1/index/TrigerInteract'
        headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
                'origin': 'https://www.bilibili.com',
                'sec-fetch-site': 'same-site',
                'cookie': self.cookies,
            }
        data ={
            'csrf':csrf,
            'interact_type':3,
            'roomid':roomid,
        }
        res = requests.post(url=url1,data=data,headers=headers).json()
        return res    

    def daka(self):
        medal_list = self.get_medal_list()
        length = len(medal_list)
        counter = 0
        for i in medal_list:
            if i not in self.black_list:
                if not self.send_msg(i,'打卡'):
                    self.send_msg(i,'(｀・ω・´)')
                for _ in range(3):
                    self.like(i)
                    time.sleep(1)
            counter += 1
            print("每日打卡:%d/%d"%(counter,length))
        print('每日打卡完成')
        length2 = len(self.share_list)
        counter2 = 0
        if length2 != 0:
            if length2 > 24:
                self.share_list = self.share_list[0:24] 
            for j in self.share_list:
                roomid = get_real_roomid(j)
                for _ in range(5):
                    self.share(roomid)
                    time.sleep(660)
                counter2 += 1 
                print("直播间分享:%d/%d"%(counter2,length2))
            print('直播间分享完成')
        else:
            print("未添加分享的直播间")

    

if __name__ == '__main__':
    lg = Login_web()
    lg.daka()
    scheduler = BlockingScheduler()
    scheduler.add_job(lg.daka,'cron',hour = 0,minute = 5,timezone='Asia/Shanghai')
    scheduler.start()
