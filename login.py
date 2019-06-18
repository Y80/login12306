'''
注意：
    1. 登录入口有两个，不同的登录入口，登录流程存在差异
        ①. https://kyfw.12306.cn/otn/resources/login.html
        ②. https://kyfw.12306.cn/otn/login/init
    2. 进行账户验证时、Cookies 中的 RAIL-DEVICEID 是必须，可以在浏览器中获取，保质期很长的，手动获取一次就可以了
'''
import time
import base64
import pickle
from io import BytesIO
import requests
from PIL import Image
from account import username, password  # 报错不用管

# 取消 urllib3 中的 https 警告
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
disable_warnings(InsecureRequestWarning)


class XX12306:
    url_is_login = 'https://kyfw.12306.cn/otn/login/conf'
    url_start_page1 = 'https://kyfw.12306.cn/otn/resources/login.html'
    url_start_page2 = 'https://kyfw.12306.cn/otn/login/init'
    url_captcha1 = 'https://kyfw.12306.cn/passport/captcha/captcha-image64?login_site=E&module=login&rand=sjrand'
    url_captcha2 = 'https://kyfw.12306.cn/passport/captcha/captcha-image?login_site=E&module=login&rand=sjrand'
    url_captcha_check = 'https://kyfw.12306.cn/passport/captcha/captcha-check'
    url_qr = 'https://kyfw.12306.cn/passport/web/create-qr64'
    url_checkqr = 'https://kyfw.12306.cn/passport/web/checkqr'
    # 用户登录经过以下四个接口验证
    url_login = 'https://kyfw.12306.cn/passport/web/login'
    url_userLogin = 'https://kyfw.12306.cn/otn/passport?redirect=/otn/login/userLogin'
    url_uamtk = 'https://kyfw.12306.cn/passport/web/auth/uamtk'
    url_uamauthclient = 'https://kyfw.12306.cn/otn/uamauthclient'

    url_user_info = 'https://kyfw.12306.cn/otn/modifyUser/initQueryUserInfoApi'  # 返回个人信息.json

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/65.0.3325.146'
    }
    proxy = {  # 用于本地抓包
        'http': 'http://127.0.0.1:8153',
        'https': 'https://127.0.0.1:8153'
    }

    # 验证码坐标
    locate = {
        '1': '44,44,',
        '2': '114,44,',
        '3': '185,44,',
        '4': '254,44,',
        '5': '44,124,',
        '6': '114,124,',
        '7': '185,124,',
        '8': '254,124,',
    }

    def __init__(self):
        self.session = requests.session()
        self.session.verify = False  # 取消验证 SSL
        self.session.headers.update(XX12306.headers)
        self.username = ''
        self.password = ''
        self.session.proxies.update(XX12306.proxy)

    def get_captcha_answer(self, use_lbl=False, captcha=None):
        if captcha:
            img_stream = BytesIO(captcha)
        else:
            rsp = self.session.get(XX12306.url_captcha2)
            img_stream = BytesIO(rsp.content)
        if use_lbl:
            # 调用验证码识别接口
            files = {'pic_xxfile': ('img.jpg', img_stream, 'image/jpeg')}  # name filename (filedata) content-type
            time.sleep(1)
            rsp = requests.post('http://littlebigluo.qicp.net:47720/', files=files, proxies=XX12306.proxy).text
            if '系统访问过于频繁' not in rsp and len(rsp) > 600:
                return rsp[rsp.find('<B>') + 3:rsp.find('</B>')]
        Image.open(img_stream).show()
        # 手动输入答案序号时，验证码的图片编号以“从左至右、从上至下”的顺序依次编号为 1-8，多项用空格分隔
        return input('请输入答案序号：')

    # 检测 littlebigluo.qicp.net:47720 是否可以正常使用
    def is_useable_littlbigluo(self):
        captcha = 'test-captcha.jpg'  # 用于测试的验证码图片路径
        files = {'pic_xxfile': ('img.jpg', open(captcha, 'rb'), 'image/jpeg')}  # name: (filename (filedata) content-type)
        rsp = requests.post('http://littlebigluo.qicp.net:47720/', proxies=XX12306.proxy, files=files).text
        return True if rsp[rsp.find('<B>') + 3:rsp.find('</B>')] == '5 7' else False

    def set_cookie_tk(self, tk):
        self.session.cookies.update({'tk': tk})

    def login_by_qr(self):
        rsp = self.session.post(XX12306.url_qr, data={'appid': 'otn'}).json()
        image = rsp['image']
        Image.open(BytesIO(base64.b64decode(image))).show()  # 显示登录二维码
        print('请用手机客户端扫描二维码登录')
        while True:
            rsp = self.session.post(XX12306.url_checkqr, {
                'uuid': rsp['uuid'],
                'appid': 'otn'
            }).json()
            if rsp['result_code'] == '1':
                print('已扫描，请确认登录')
            elif rsp['result_code'] == '2':
                print('√ 扫码登陆成功')
                break
            time.sleep(1)

        self.session.get(XX12306.url_userLogin)
        rsp = self.session.post(XX12306.url_uamtk, data={'appid': 'otn'}).json()
        rsp = self.session.post(XX12306.url_uamauthclient, data={'tk': rsp['newapptk']}).json()
        if rsp['result_message'] != '验证通过':
            print('\n\n\n扫码登录登录失败！')
            exit()
        print('😀此账户已成功登录！\n\n\n')

    def login(self, username, password):
        self.session.cookies.update({
            'RAIL_DEVICEID': 'UB_YPPl2eqm67m7qb5gO94qDunov_zXkUjVBnT9xSUxUQ5N1bhc8KBFm0t_KaZ1T-GvG-zDvQyRiCRysTeW4Pof3ZwyDv64H9lstE3ht_n9QKEkRZmQwfgValcEWSVXydcmd_xuRxfrLX8n5ryxVtL2e0RtAcWnq'
        })

        use_lbl = self.is_useable_littlbigluo()
        try_count = 1

        while True:
            print('正在进行第 %d 次验证码验证' % try_count)
            try_count += 1
            use_lbl = False if try_count > 3 else use_lbl
            answer = ''
            for i in self.get_captcha_answer(use_lbl).split(' '):
                answer += self.locate[i]
            rsp = self.session.post(XX12306.url_captcha_check, params={
                'answer': answer[:-1],
                'login_site': 'E',
                'rand': 'sjrand'
            }).json()
            print(rsp['result_message'])
            if rsp['result_code'] == '4':  # 验证码校验成功
                break
            else:
                print('请重试😀')

        # 验证账户密码是否正确
        rsp = self.session.post(XX12306.url_login, data={
            'username': username,
            'password': password,
            'appid': 'otn'
        })
        if rsp.status_code != 200:
            print('\n😭登录失败——STEP 1',)
            exit()
        # 三步必须的登录流程
        self.session.get(XX12306.url_userLogin)
        rsp = self.session.post(XX12306.url_uamtk, data={'appid': 'otn'}).json()
        rsp = self.session.post(XX12306.url_uamauthclient, data={'tk': rsp['newapptk']}).json()
        if rsp['result_message'] != '验证通过':
            print('\n😭登录失败——STEP 4')
            exit()
        print('😀此账户已成功登录！\n\n\n')

    def login_by_chromedriver(self, username, password):
        from selenium import webdriver

        def get_browser():
            options = webdriver.ChromeOptions()
            # options.add_argument('--headless')
            options.add_argument('--incognito')
            options.add_argument('"--allow-running-insecure-content",')
            options.add_argument('"--disable-gpu"')
            browser = webdriver.Chrome('D:/Python36/chromedriver.exe', chrome_options=options)
            return browser

        # 将网页截图裁剪到验证码的区域，保存此验证码。使用验证码识别接口时会用到此方法。
        def save_captcha():
            img = Image.new(mode='RGB', size=(captcha.size['width'], captcha.size['height']), color='black')
            img.paste(im=Image.open(BytesIO(base64.b64decode(browser.get_screenshot_as_base64()))),
                      box=(-captcha.location['x'], -captcha.location['y']))
            img.save('captcha.jpg')
            img.close()
            # img.resize((img.size[0] * 3, img.size[1] * 3), Image.ANTIALIAS).show()

        browser = get_browser()
        browser.get(XX12306.url_start_page2)
        # captcha = browser.find_element_by_xpath('//*[@id="loginForm"]/div/ul[2]/li[4]/div/div/div[3]/img')
        # browser.execute_script("document.querySelector('#randCode').setAttribute('value','%s')" % (answer[:-1]))
        browser.find_element_by_xpath('//*[@id="username"]').send_keys(username)
        browser.find_element_by_xpath('//*[@id="password"]').send_keys(password)
        input('请在网页中进行验证，回车继续……')
        browser.find_element_by_xpath('//*[@id="loginSub"]').click()  # 登录
        # 等待网页跳转
        while browser.current_url != 'https://kyfw.12306.cn/otn/view/index.html':
            time.sleep(0.1)
        tk = browser.get_cookie('tk').get('value')
        browser.close()
        self.set_cookie_tk(tk)

    # 验证当前会话是否已登录
    def is_login(self):
        # 调用此接口需要 RAIL-DEVICEID
        rsp = self.session.post(XX12306.url_is_login).json()
        return True if rsp.get('data').get('is_login') == 'Y' else False

    def get_user_info(self):
        rsp = self.session.post(XX12306.url_user_info).json()
        if rsp['httpstatus'] == 200:
            data = rsp['data']
            userDTO = data['userDTO']
            loginUserDTO = userDTO['loginUserDTO']
            studentInfoDTO = userDTO['studentInfoDTO']
            rst = {
                'BornDate':    data['bornDateString'],
                'UserType':    data['userTypeName'],
                'IdType':      loginUserDTO['id_type_name'],  # 证件类型
                'Name':         loginUserDTO['name'],
                # 'IP':      loginUserDTO['userIpAddress']  # 通过二维码登录后调用接口才有此项
            }
            return {
                '用户信息': loginUserDTO,
                '学生信息': studentInfoDTO
            }
        else:
            return '获取个人信息失败'

    def pickle(self):
        pickle.dump(obj=self, file=open('./obj/'+self.username, 'wb'))

    def unpickle(self, username):
        t = type(self)
        self = pickle.load(open('./obj/' + username, 'rb'))
        if not isinstance(self, t):
            print('反序列化失败')
            exit()

if __name__ == '__main__':
    client = XX12306()
    # client.login_by_chromdriver(username, password)
    client.login(username, password)
    # client.set_cookie_tk('IVD01YrtcAZShiRho9zSvr5gk8OBA4T7duURTgcgz1z0')
    # print(client.is_login())
    print(client.get_user_info())
