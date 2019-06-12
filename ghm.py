#! /usr/bin/python3.4
# -*- coding: utf-8 -*-
import requests
import asyncio, os, json, time
import jinja2
import aiohttp_jinja2
import urllib.request
import configparser
import threading
import RPi.GPIO as GPIO
from aiohttp import web
ttim=0
t=object
worktime=time.time()

ver='20190612'
stapwd='abc'
setpwd='ghm2019'
softPath='/home/pi/ghm/'

kconfig=configparser.ConfigParser()
if os.path.exists(softPath+"setting.ini"):
    kconfig.read(softPath+"setting.ini")
else:
    f = open(softPath+"setting.ini", 'w')
    f.close()
    kconfig.read(softPath+"setting.ini")
    kconfig.add_section('gh')
    kconfig.write(open(softPath+"setting.ini","w"))

try:
    shell_ud_t1_set=kconfig.getint("gh","shell_ud_t1_set")
except:
    kconfig.add_section('gh')
    shell_ud_t1_set=2000
    kconfig.set("gh","shell_ud_t1_set",str(shell_ud_t1_set))

try:
    shell_ud_t2u_set=kconfig.getint("gh","shell_ud_t2u_set")
except:
    shell_ud_t2u_set=9000
    kconfig.set("gh","shell_ud_t2u_set",str(shell_ud_t2u_set))

try:
    shell_ud_t2d_set=kconfig.getint("gh","shell_ud_t2d_set")
except:
    shell_ud_t2d_set=7000
    kconfig.set("gh","shell_ud_t2d_set",str(shell_ud_t2d_set))

try:
    shell_ud_t3_set=kconfig.getint("gh","shell_ud_t3_set")
except:
    shell_ud_t3_set=5000
    kconfig.set("gh","shell_ud_t3_set",str(shell_ud_t3_set))

try:
    spdu=kconfig.getint("gh","spdu")
except:
    spdu=50
    kconfig.set("gh","spdu",str(spdu))

try:
    spdd=kconfig.getint("gh","spdd")
except:
    spdd=50
    kconfig.set("gh","spdd",str(spdd))

try:
    stapwd = kconfig.get("gh","stapwd")
except:
    stapwd = 'abc'
    kconfig.set("gh","stapwd",stapwd)

try:
    sn = kconfig.get("gh","sn")
except:
    sn = 'gh001'
    kconfig.set("gh","sn",sn)

kconfig.write(open(softPath+"setting.ini","w"))


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
io_dy=23 #锅炉电源
io_zq=24 #蒸汽
GPIO.setup(io_dy, GPIO.OUT)
GPIO.setup(io_zq, GPIO.OUT)
GPIO.output(io_dy, 1)
GPIO.output(io_zq, 1)
'''
io_in1=12
GPIO.setup(io_in1,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
I_prot=0
'''
moto_1_p=13 #脉宽输出
moto_1_f=19 #正转
moto_1_r=26 #反转
GPIO.setup(moto_1_f, GPIO.OUT)
GPIO.setup(moto_1_r, GPIO.OUT)
GPIO.setup(moto_1_p, GPIO.OUT)
p = GPIO.PWM(moto_1_p, 1500)
p.start(0)


seled_cai='NA'
watchdog=0
eTimer1=False
eIntval1=5
sta_shell=0
shell_up_down=0
settemp=0
guolupower=0
running_sta='0'
timediff=0
time_end=0
'''
sta_shell
0 top stop
1 running
2 bottom stop

shell_up_down
0 to up
2 to bottom

running_sta
0 stop
1 running

seled_cai
0 main list
1-10 cai item
'''


from os import system
#system('sudo ifdown wlan0')#停用网卡
import pexpect
import re
from threading import Thread
from time import sleep

'''
class WAM_AP(object):
    def _get_end(self):
        while True:
            sleep(5)
    def __init__(self):
        self._process = pexpect.spawn('sudo create_ap --no-virt -g 192.168.2.105 wlan0 eth0 '+sn+' 66341703')
        self._end_thread = Thread(target=self._get_end)
        self._end_thread.start()
WAM_AP()
'''

@asyncio.coroutine
def return_sta(request):
    global eTimer1,eIntval1,watchdog,running_sta
    global shell_up_down,sta_shell,guolupower,settemp,timediff
    global stapwd,setpwd,softPath,tempeture_1,tempeture_2,ttim,t
    global ttfinck,worktime,seled_cai
    global shell_ud_t1_set,shell_ud_t2u_set,shell_ud_t2d_set,shell_ud_t3_set
    global spdu,spdd,ver,sn

    hhdd=[('Access-Control-Allow-Origin','*'),('Content-Type','application/json')]
    po = yield from request.post()
    #if po['p'] == stapwd:
    if 1:

        if po['m'] == 'sta':
            watchdog=0
            tbody= '{"shell_sta":'+str(sta_shell)
            tbody+= ',"guolupower":'+str(guolupower)
            tbody+= ',"settemp":'+str(settemp)
            tbody+= ',"timediff":'+str(timediff)
            tbody+= ',"running_sta":'+str(running_sta)
            tbody+= ',"ttfinck":'+str(ttfinck)
            tbody+= ',"wt":'+str(int(time.time()-worktime))
            tbody+= ',"cai":"'+(seled_cai)+'"'
            tbody+= ',"tmp1":'+str(tempeture_1)+'}'
            return web.Response(headers=hhdd ,body=tbody.encode('utf-8'))

        elif po['m'] == 'sel_cai':
            seled_cai=po['cai']
            tbody= '{"sel_cai":"ok"}'
            return web.Response(headers=hhdd ,body=tbody.encode('utf-8'))

        elif po['m'] == 'addtime':
            watchdog=0
            #print('old stop at'+str(eIntval1))
            eIntval1+=int(po['d'])
            #print('shall stop at '+str(eIntval1))
            #tbody= '{"addtime":'+str(eIntval1-int(time.time()))+'}'
            tbody= '{"addtime":"ok"}'
            return web.Response(headers=hhdd ,body=tbody.encode('utf-8'))

        elif po['m'] == 'settemp':
            settemp=0
            running_sta=po['d']
            if po['ttmp']== 'xh':
                ttmp=b'\x02\x06\x10\x01\x03\xD4\xDC\x56'
                settemp=98
            if po['ttmp']== 'zh':
                ttmp=b'\x02\x06\x10\x01\x04\x60\xDE\x11'
                settemp=112
            if po['ttmp']== 'dh':
                ttmp=b'\x02\x06\x10\x01\x05\x14\xDF\xA6'
                settemp=130
            try:
                ser = serial.Serial("/dev/ttyUSB0",parity=serial.PARITY_ODD,timeout=1)
                ser.write(ttmp)
                recv = ser.read(8)
                #print(recv)
                ser.close()
            except e:
                pass

            tbody= '{"settemp":"'+po['ttmp']+'"}'
            return web.Response(headers=hhdd ,body=tbody.encode('utf-8'))

        elif po['m'] == 'gpioon':
            if po['d']== 'dy':
                guolupower=1
                GPIO.output(io_dy, 0)
                tbody= '{"dy":"on"}'
            print(tbody)
            return web.Response(headers=hhdd ,body=tbody.encode('utf-8'))

        elif po['m'] == 'gpiooff':
            if po['d']== 'dy':
                guolupower=0
                GPIO.output(io_dy, 1)
                tbody= '{"dy":"off"}'
            elif po['d']== 'zq':
                if sta_shell==1:
                    t.cancel()
                    p.ChangeDutyCycle(0)
                    sta_shell=0
                    GPIO.output(moto_1_r, 1)
                    GPIO.output(moto_1_f, 1)

                eIntval1=time.time()
                GPIO.output(io_zq, 1)
                tbody= '{"zq":"off"}'
            print(tbody)
            return web.Response(headers=hhdd ,body=tbody.encode('utf-8'))

        elif po['m'] == 'shell':
            tbody= '{"a":"shell","b":"noaction"}'
            if po['d']== 'up':
                shell_up()
                tbody= '{"shell":"up"}'
            elif po['d']== 'dw':
                shell_dw()
                running_sta=1
                eIntval1=int(time.time())+int(po['dltime'])
                tbody= '{"shell":"dw"}'
            elif sta_shell==1:
                ttfin()
                tbody= '{"a":"shell","b":"stop"}'
            print(tbody)
            ttim=time.time()
            return web.Response(headers=hhdd ,body=tbody.encode('utf-8'))

        elif po['m'] == 'gset':
            tbody = '{"get":"set",'
            tbody+= '"t1":"'+str(shell_ud_t1_set)+'",'
            tbody+= '"t2u":"'+str(shell_ud_t2u_set)+'",'
            tbody+= '"t2d":"'+str(shell_ud_t2d_set)+'",'
            tbody+= '"t3":"'+str(shell_ud_t3_set)+'",'
            tbody+= '"spdu":"'+str(spdu)+'",'
            tbody+= '"spdd":"'+str(spdd)+'",'
            tbody+= '"ver":"'+ver+'",'
            tbody+= '"sn":"'+str(sn)+'"}'
            return web.Response(headers=hhdd ,body=tbody.encode('utf-8'))

        elif po['m'] == 'wset':
            shell_ud_t1_set=int(po['t1'])
            shell_ud_t2u_set=int(po['t2u'])
            shell_ud_t2d_set=int(po['t2d'])
            shell_ud_t3_set=int(po['t3'])
            spdu=int(po['spdu'])
            spdd=int(po['spdd'])
            sn=po['sn']
            kconfig.set("gh","shell_ud_t1_set",po['t1'])
            kconfig.set("gh","shell_ud_t2u_set",po['t2u'])
            kconfig.set("gh","shell_ud_t2d_set",po['t2d'])
            kconfig.set("gh","shell_ud_t3_set",po['t3'])
            kconfig.set("gh","spdu",po['spdu'])
            kconfig.set("gh","spdd",po['spdd'])
            kconfig.set("gh","sn",po['sn'])
            kconfig.write(open(softPath+"setting.ini","w"))
            tbody= '{"p":"ok","w":"ok"}'
            return web.Response(headers=hhdd ,body=tbody.encode('utf-8'))

        elif po['m'] == 'reboot':
            system('sudo reboot')

        elif po['m'] == 'upgrade':
            tbody= '更新成功'
            #if po['tp']=='core':
            try:
                upedfile=po['cfile']
                ufilename = upedfile.filename
                ufilecont = upedfile.file
                content = ufilecont.read()
                with open(softPath+ufilename, 'wb') as f:
                    f.write(content)
            except:
                tbody='上传文件打开失败'
            #解压缩
            try:
                fz = zipfile.ZipFile(softPath+"core.zip",'r')
                for file in fz.namelist():
                    fz.extract(file,softPath)
                fz.close()
            except:
                tbody='解压失败'
            return web.Response(headers=hhdd ,body=tbody.encode('utf-8'))

    else:
        tbody= '{"p":"error"}'
        return web.Response(headers=hhdd ,body=tbody.encode('utf-8'))


def shell_dw():
    global t,shell_up_down,sta_shell,eIntval1
    try:
        t.cancel()
    except:
        pass
    print('shell dw')
    t = threading.Timer(shell_ud_t1_set/1000, tt2)
    GPIO.output(moto_1_r, 1)
    GPIO.output(moto_1_f, 0)
    p.ChangeDutyCycle(100)
    t.start()
    shell_up_down=2
    sta_shell=1

def shell_up():
    global t,shell_up_down,sta_shell
    try:
        t.cancel()
    except:
        pass
    print('shell up')
    t = threading.Timer(shell_ud_t1_set/1000, tt2)
    GPIO.output(moto_1_r, 0)
    GPIO.output(moto_1_f, 1)
    p.ChangeDutyCycle(100)
    t.start()
    shell_up_down=0
    sta_shell=1


def self_tt1():
    global ttfinck
    global t,shell_ud_t1_set,shell_up_down,ttim
    t = threading.Timer(shell_ud_t1_set/1000, tt2)
    GPIO.output(moto_1_r, 0)
    GPIO.output(moto_1_f, 1)
    p.ChangeDutyCycle(100)
    t.start()
    ttfinck=0
    shell_up_down=0
    sta_shell=1
    print('self_tt1 '+str(ttim-time.time()))

def tt2():
    global ttfinck
    global t,shell_ud_t2d_set,shell_ud_t2u_set,shell_up_down,ttim
    if shell_up_down==0:
        shell_t2=shell_ud_t2u_set/1000
    else:
        shell_t2=shell_ud_t2d_set/1000
    t = threading.Timer(shell_t2, tt3)
    p.ChangeDutyCycle(100)
    t.start()
    ttfinck=0
    print('tt2 '+str(ttim-time.time()))

def tt3():
    global ttfinck
    global t,shell_ud_t3_set,shell_up_down,ttim,spdu,spdd
    if shell_up_down==0:
        p.ChangeDutyCycle(spdu)
    else:
        p.ChangeDutyCycle(spdd)
    t = threading.Timer(shell_ud_t3_set/1000, ttfin_before)
    t.start()
    ttfinck=0
    print('tt3 '+str(ttim-time.time()))

ttfinck=0
def ttfin_before():
    global ttfinck
    ttfinck=1
    ttfin()

def ttfin():
    global t,ttim,sta_shell,shell_up_down,moto_1_r,moto_1_f
    global running_sta,eTimer1,eIntval1,ttim

    t.cancel()
    p.ChangeDutyCycle(0)
    sta_shell=shell_up_down
    GPIO.output(moto_1_r, 1)
    GPIO.output(moto_1_f, 1)
    print('shell run end '+str(ttim-time.time()))

    if sta_shell==2:
        running_sta=1
        eTimer1=True
        #eIntval1=int(time.time())+int(delaytime)
        ttim=time.time()
        print('zq eTimer1 start')
        GPIO.output(io_zq, 0)


import zipfile
@asyncio.coroutine
def sys_update(request):
    global softPath
    hhdd=[('Access-Control-Allow-Origin','*'),('Content-Type','application/json')]
    posted = yield from request.post()
    #print(posted)
    tbody= '成功'
    #if posted['tp']=='core':
    try:
        upedfile=posted['cfile']
        ufilename = upedfile.filename
        ufilecont = upedfile.file
        content = ufilecont.read()
        with open(softPath+ufilename, 'wb') as f:
            f.write(content)
    except:
        tbody='上传文件打开失败'
    #解压缩
    try:
        fz = zipfile.ZipFile(softPath+"core.zip",'r')
        for file in fz.namelist():
            fz.extract(file,softPath)
        fz.close()
    except:
        tbody='解压失败'
    return web.Response(headers=hhdd ,body=tbody.encode('utf-8'),content_type='application/json')


@aiohttp_jinja2.template('upgrade.html')
def upgrade(request):
    #使用aiohttp_jinja2  methed 2
    global sn,ver
    return {'html': 'upgrade','sn': sn,'ver': ver}


import serial
tempeture_1=0
@asyncio.coroutine
def get_temp():
    global tempeture_1,ser
    tt1=0
    while True:
        # 打开串口 发送 获得接收缓冲区字符
        try:
            ser = serial.Serial("/dev/ttyUSB0",parity=serial.PARITY_ODD,timeout=1)
            try:
                ser.write(b'\x02\x03\x10\x00\x00\x04\x40\xFA')
                recv = ser.read(7)
                #print(recv)
                if recv and recv[2]==8:
                    tt1=(recv[3]*255+recv[4])/10
                else:
                    #print(recv)
                    tt1=0.2
            except:
                tt1=0.3

            try:
                ser.close()
            except:
                tt1=0.4
                pass

        except:
            tt1=0.1

        yield from asyncio.sleep(0.5)
        tempeture_1=tt1
        #print(tempeture_1)


@asyncio.coroutine
def loop_info():
    global eTimer1,eIntval1,sta_shell,running_sta
    global watchdog,ttim,time_end
    global t,p,timediff
    #global I_prot
    while True:
        yield from asyncio.sleep(0.05)
        '''
        watchdog+=1
        if watchdog>100:
            watchdog=0
            print('watchdog')
            #GPIO.output(io_zq, 1)
        '''
        if eTimer1==True:
            #sta_shell=1
            timediff=int(time.time())-int(eIntval1)
            #print('timediff ',timediff)
            time_end=0
            if timediff>0:
                timediff=0
                sta_shell=2
                running_sta=0
                time_end=1
                GPIO.output(io_zq, 1)
                print('eTimer1 end '+str(time.time()-ttim))
                eTimer1=False
                shell_up()

    return 1


def tt_prot():
    global t,sta_shell
    sta_shell=0
    p.ChangeDutyCycle(0)
    print('protect fin '+str(time.time()))


@asyncio.coroutine
def init(loop):
    global softPath,ver
    app = web.Application(loop=loop)
    #使用aiohttp_jinja2
    aiohttp_jinja2.setup(app,loader=jinja2.FileSystemLoader(softPath+'tpl'))
    app.router.add_route('POST', '/sta', return_sta)
    #app.router.add_route('POST', '/setting', setting)
    app.router.add_route('*', '/sys_update', sys_update)
    app.router.add_route('*', '/upgrade', upgrade)
    srv = yield from loop.create_server(app.make_handler(), '0.0.0.0', 9001)
    print(' ghm started at http://9001... '+ver)
    return srv

loop = asyncio.get_event_loop()
tasks = [init(loop), loop_info(), get_temp()]#loop_info持续发送状态
loop.run_until_complete(asyncio.wait(tasks))
loop.run_forever()
