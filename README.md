# 提供以下几种方式登录12306

- `login()` 登录 12306 最快捷的方式
- `login_by_qr()` 通过手机客户端扫描二维码登录
- `set_cookie_tk()` 先在浏览其中登录 12306，然后取得 cookie 中的 tk 项即可
- `login_by_chromedriver()` 通过 selenium + chromedriver 登录

#
登录成功的对象可以序列化至本地，以便远端或之后反序列化此文件，直接得到一个已登陆的会话对象。

#
调用 `login()` 和 `is_login()` 方法时，必须设置一项 cookie —— `RAIL_DEVICEID`。  
获取 `RAIL_DEVICEID` 最快捷的方式时用浏览器打开任意一个 12306 站点（如：https://www.12306.cn/index/index.html ），然后在 12306.cn 域名中获得此 cookie。  
也可以通过抓包，查看 .js 文件，自己构造请求参数，向 https://kyfw.12306.cn/otn/HttpZF/logdevice 发送 QueryString，获取到的 json 文件中的 'dfp' 项即可作为 `RAIL_DEVICEID`。

#
请在 `account.py` 正确填写 12306 的账户、密码。
