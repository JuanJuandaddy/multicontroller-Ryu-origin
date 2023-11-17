# -*-coding:utf-8-*-
import math
import time
import random
import exp_conf
import re
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import  RemoteController
from mininet.node import  Host
from mininet.node import OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink#设置链路带宽的选项
from subprocess import Popen
from multiprocessing import Process
import numpy as np
import settings
from alive_progress import alive_bar
from threading import Thread
"""
此为单连接多控制器，表示每个控制器仅仅连接到自己的交换机，与其他控制器的交换机不存在连接关系
"""
class multicon_topo(Topo):
    #可选参数的值为sw_link，sw_host,switches,hosts,分别代表ovs之间的连接链路，连接了主机的ovs，所有ovs列表，所有主机列表
    #均与controller中的控制器进行对齐
    #参数形式为multicon_topo('127.0.0.1','OpenFlow13',['c1','c2'],[6653,6654],{tuple(sw1,sw2):[port1,port2]},{acc_sw:host}，
    # [[s1,s2...],[sj,sj+1...]],[[h1,h2...],[hj,hj+1...]])
    def __init__(self, remote_ip, ofp_version, controllers, ports, *args, **kwargs):
        self.net=Mininet(controller=RemoteController)
        self.ip=remote_ip
        self.version=ofp_version
        self.cons=controllers
        self.ports=ports
        self.con_obj=[]
        self.sw_obj=[]
        self.ping_dict=[]
        self.args=kwargs#传递的多余参数列表，类型为tuple，**kwargs为字典
        self.subnets=self.split_controllers()#子网ID

    def split_controllers(self): #返回控制器数目，作为子网数，子网ID由控制器ID为主
        subnets=[]
        for c in self.cons:
            subnets.append(list(c)[1])
        return subnets

    def create_controller(self):
        for index,c in enumerate(self.cons):
            con=self.net.addController(c,controller=RemoteController,ip=self.ip,port=self.ports[index])
            self.con_obj.append(con)

    def create_switch(self):#创建交换机实例
        for index,sw in enumerate(self.args["switches"]):
            sws=[]
            for s in sw:
                s=self.net.addSwitch(s,protocols=self.version,cls=OVSKernelSwitch)
                sws.append(s)
            self.sw_obj.append(sws)

    def create_host(self):
        for index,host in enumerate(self.args["hosts"]):#[h1,h2,h3...]

            for i,h in enumerate(host):#h=[h1001,h1002,h1003]  i=0   h=[h1101,h1102,h1103]

                single_sw_host_num = len(h) #单个交换机下连接的主机数目  例：3个

                for ind,hos in enumerate(h):

                    last_addr=str(single_sw_host_num*i+ind+1)

                    h=self.net.addHost(hos,cls=Host,ip="192.168."+self.subnets[index]+"."+last_addr)

    def create_link(self):
        #创建主机与ovs连接的链路，ovs连接host的端口为5以上，5以下端口已经被交换机连接占用故以10开始,不可以为0，0为环回口会导致不通，没有arp报文

        for sw,host in self.args["sw_host"].items():
            start_port = 10
            for h in host:

                start_port+=1

                self.net.addLink(sw,h,start_port)

        #创建ovs之间的连接链路,不指定端口，指定端口可以在settings文件中的SW_LINK选项进行指定,port可用可不用
        for sw,port in self.args["sw_link"].items():
            self.net.addLink(sw[0],sw[1],port[0],port[1])

    def start_sw_con(self):
        for index in range(len(self.con_obj)):
            for sw in self.sw_obj[index]:
                sw.start([self.con_obj[index]])

    def start_con(self):
        for con in self.con_obj:
            con.start()

    def build_topo(self):

        self.create_controller()

        self.create_host()

        self.create_switch()

        self.create_link()

    def ping_all(self):
        #让server和控制器在网络初期初始化阶段完成对网络内所有主机的辨别
        #如果需要新加入主机，ping一次加入主机所在的area的其他主机，让控制器与server学习即可
        #需要完成域内互ping、跨域互ping
        hosts=self.args["hosts"]

        area_num=len(hosts)

        print("|", "Area-In Ping Start !".center(50, "="), "|")
        # 域内ping
        for area_id in range(area_num):

            # 域内ping
            self.area_in_ping(hosts[area_id])

        print("|", "Wait {}s For Next Operation !".center(50, "=").format(settings.PING_IN_OUT_INTERVAL), "|")

        if settings.PING_OUT_MODE:
            print("|", "Area-Out Ping Start !".center(50,"="), "|")
            # 跨域ping
            for area_id in range(area_num):

                mirror_hosts=hosts.copy()

                mirror_hosts.pop(area_id)

                for h in hosts[area_id]:

                    self.area_out_ping(h,mirror_hosts)

            self.ping_dict.clear()

    def area_out_ping(self,h,other_hosts):

        for other_host in other_hosts:

            for d in other_host:

                if [h,d] in self.ping_dict or [d,h] in self.ping_dict:

                    continue

                else:

                    self.ping(h,d)

                    self.ping_dict.append([h,d])

                    self.ping_dict.append([d, h])

    def area_in_ping(self,hosts):

        length = len(hosts)

        if length % 2 == 0:
            for f, t in zip(hosts[:int(length / 2)], hosts[int(length / 2):]):

                self.ping(f,t)
        else:
            f_index = math.floor(length / 2)

            t_index = math.ceil(length / 2)

            for f, t in zip(hosts[:f_index], hosts[t_index:]):

                self.ping(f,t)

            self.ping(hosts[f_index],hosts[0])

    def ping(self,src,dst):

        #print(f'{src} ==> {dst}')

        src_obj,dst_obj=self.net.get(src),self.net.get(dst)

        ping_ip=dst_obj.IP()#获取目的主机的IP地址

        ping_args=f'ping -c {str(settings.PING_NUM)} {ping_ip} &' #   &就是执行命令，按下回车的意思

        src_obj.cmd(ping_args)

        time.sleep(settings.PING_INTERVAL)

    def start_pktin(self):
        threads=[]

        hosts = self.args["hosts"]

        TRANSFORM_FACTOR = 26

        controller_load=exp_conf.CONTROLLER_OVERLOAD

        controllers=[controller for controller in controller_load.keys()]

        for controller in controllers:

            controller_num = int(controller.split('C')[1]) - 1

            hs = hosts[controller_num]

            hs.pop(0)

            SUM_PKTIN = controller_load[controller]["RATE"] * settings.CONTROLLER_PKT_THRESHOLD

            SUM_THREAD_NUM = int(SUM_PKTIN / TRANSFORM_FACTOR)

            RES = self.distribute_thread(SUM_THREAD_NUM, len(hs) * settings.EACH_SW_HOSTS_NUM)

            def s(hs,RES):
                for host, thread in zip(hs, RES):

                    for h, t in zip(host, thread):

                        order = re.findall("\d+", h)[0]

                        h_obj=self.net.get(h)

                        command_args=f'python3 pktin.py {order} {t} &'

                        h_obj.cmd(command_args)

                        time.sleep(1)

            t = Thread(target=s, args=(hs, RES,))

            t.start()

            threads.append(t)

        for th in threads:
            th.join()

    def distribute_thread(self,thread_num, host_num):

        return self.div_arr(self.get_random_red_packet(thread_num, host_num), settings.EACH_SW_HOSTS_NUM)

    def get_random_red_packet(self,total_amount, quantities):
        # 发红包逻辑
        amount_list = []
        person_num = quantities
        cur_total_amount = total_amount
        for _ in range(quantities - 1):
            amount = random.randint(0, cur_total_amount // person_num * 2)
            # 每次减去当前随机金额，用剩余金额进行下次随机获取
            cur_total_amount -= amount
            person_num -= 1
            amount_list.append(amount)
        amount_list.append(cur_total_amount)
        return amount_list

    def div_arr(self,arr, num):
        step = 0
        res = []
        for _ in range(len(arr) // num):
            res.append(arr[step:step + num])
            step = step + num
        return res

    def mirror_cli(self):
        while 1:
            command=input("mininet> ")
            if command=='s':
                self.start_pktin()
            if command=='cli':
                self.CLI()
                break

    def CLI(self):

        CLI(self.net)

    def stop(self):

        self.net.stop()

def run(ip,version,cons,ports,swl,swh,sws,h):

    topo=multicon_topo(
        remote_ip=ip,ofp_version=version,controllers=cons,ports=ports,
        sw_link=swl,sw_host=swh,switches=sws,hosts=h
    )
    topo.build_topo()

    topo.net.build()

    topo.start_sw_con()

    topo.start_con()

    # print("|", "OS3E Has Been Built Successfully !".center(50, "="), "|")
    #
    # print("|", "Waiting {}s For Stable Initiation !".center(50, "=").format(settings.WAITING_FOR_STABLE_NETWORK_SECONDS), "|")
    #
    # time.sleep(settings.WAITING_FOR_STABLE_NETWORK_SECONDS)
    #
    # print("|", "Testing Pingall !".center(50, "="), "|")
    #
    # topo.ping_all()
    #
    # print("|", "Network Correspondence Success !".center(50, "="), "|")

    #topo.mirror_cli()

    topo.CLI()

    topo.stop()

if __name__ == '__main__':
    IP=settings.CONTROLLER_IP #控制器IP

    OFP_VERSION=settings.OFP_VERSION #openflow版本

    CONTROLLERS=settings.CONTROLLERS #控制器ID，代表有子网0和子网1，代表着有area0和area1两个控制area，
                            # 在Ryu源码中该配置极其重要，务必2者保持一致

    PORTS=settings.CONTROLLER_PORTS #控制器端口

    EDGE_LINK=settings.EDGE_LINK#边缘交换机的连接端口，用于Server对全局拓扑的初始化

    SW_LINK=settings.SW_LINK#交换机之间的链路

    SW_LINK.update(EDGE_LINK)#加入边界链路

    SW_HOST=settings.SW_HOST#交换机与主机之间的映射

    SWS=settings.SWS#全体交换机，区分控制器

    HOSTS=settings.HOSTS#全体主机，区分控制器

    run(IP,OFP_VERSION,CONTROLLERS,PORTS,SW_LINK,SW_HOST,SWS,HOSTS)

