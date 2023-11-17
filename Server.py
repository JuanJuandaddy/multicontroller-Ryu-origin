#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
该类只负责创建一个Server连接，消息处理交给Client类
"""
import logging
import networkx as nx
from gevent import monkey;monkey.patch_all()
import socket
import time
import contextlib
import json
from Client import Client
from gevent import spawn
from threading import Thread
from StreamInfo import InfoProcess
import settings

"""
服务初始信息
"""
IP=settings.IP     #IP

PORT=settings.PORT          #端口号

WAIT_CONNECT=settings.WAIT_CONNECT  #最大等待连接数

WRINTE_PKTIN_LOAD_MONITOR=settings.WRINTE_PKTIN_LOAD_MONITOR     # 获取pktin负载的周期

"""
    controller_id 每一个控制器的IP从0开始，具体从几开始，要看网络的子网号，具体请看mininet拓扑文件中的配置信息
"""


class Server(object):
    def __init__(self, *args):
        #初始化服务类
        super(Server, self).__init__()

        self.controller_id = 0 #控制器ID从1开始

        self.controller_obj={}

        self.server = self.start_server()

        self.log=InfoProcess()

        #全局信息类
        self.switches={}#交换机从属表 {dpid:master_controller|area_id}

        self.topo={}#拓扑信息 {(dpid,dpid):(port,port)}

        self.paths={}#全域路径表 {(ip_src,ip_dst):[path]}  只有最短路径

        self.dpaths={}#全域路径表{(src_dpid,dst_dpid):[path]} 只有最短路径

        self.sw_ip={}#全局IP-主机-Area映射表 {(sw,port):{"ip":xxxx,"area_id":xx}}

        self.edge_sw={}#边界交换机 {(dpid,port):area_id} 边界交换机端口所对应的area

        self.arp_table={}#全局mac地址对应 {ip:mac}

        self.FLOOD_IP=[]#全局FLOOD代理表，{controller_id:[ip1....ipn]}

        #全局负载类
        self.controller_load={} #{c1:load}

        self.controller_pktin_load={}    #{c1:{pktin:xxx,delay:xxx}}

        self.switches_pktin_load={}  #{c1:{sw1:{pktin_speed:xxx,percentage：xxx,pktin_size:xxx}....}}


        #拓扑计算类
        self.graph=nx.DiGraph()

        #拓扑初始化类
        self.init_edge_link()

    #========初始化TOPO========
    """
        由于不同控制area的边界控制器判断逻辑失误，所以直接送setting中的EDGE_LINK进行初始化
    """
    def init_edge_link(self):
        for sw,port in settings.EDGE_LINK.items():
            src_dpid, dst_dpid, src_port, dst_port = int(sw[0].split('s')[1]), int(sw[1].split('s')[1]), port[0], port[1]
            self.graph.add_edge(src_dpid, dst_dpid,src_port=src_port,dst_port=dst_port)
            self.graph.add_edge(dst_dpid, src_dpid, src_port=dst_port, dst_port=src_port)
            self.topo[(src_dpid, dst_dpid)] = (src_port, dst_port)
    #========初始化服务器========
    def start_server(self):
        server=socket.socket()
        server.bind((IP,PORT))
        server.listen(WAIT_CONNECT)
        return server

    def accept_client(self):
        while True:
            controller, addr = self.server.accept()  # 为每一个client保存为一个对象，返回每一个操控该客户端的socket句柄，也就是client
            # t=self.thread_exec.submit()
            self.controller_id += 1
            thread = Thread(target=self.start_client, args=(controller, addr))
            #thread.setDaemon(True)  # 主进程结束，该守护进程结束
            thread.start()

    def start_client(self,controller,addr):
        self.log.warning(f'{addr} has connected!!')
        with contextlib.closing(Client(controller)) as c:
            c.status=True#状态设为已连接
            c.server=self
            c.cur_id=self.controller_id
            self.controller_obj[self.controller_id-1] = c#存储controller的消息处理
            c.set_controller_id()
            c.start_spawn()

    def remove_client(self,controller_id):
        """
        :param controller_id: 控制器ID
        :return: 控制器下线
        """
        controller=self.controller_obj[controller_id]
        if controller:
            controller.close()
            self.controller_obj.pop(controller_id)
            print(f'控制器：{controller_id}  下线！')

    def start(self):

        #spawn(self.monitor)  # 协程监控，打印全局拓扑

        spawn(self.write_pktin_load) #记录pktin负载

        print("Server start...")

    def write_pktin_load(self):
        while True:
            if self.controller_pktin_load:

                for cid in self.controller_pktin_load.keys():

                    with open(f"/home/ryu/multicontroller/zoomulti/performance/speed_delay/controller_{cid}","w+") as f:

                        f.writelines(f'cid={cid}\ntotal_pkt_speed={self.controller_pktin_load[cid]["pktin"]}\ntotal_pkt_delay={self.controller_pktin_load[cid]["delay"]}\n')

                        for sws in self.switches_pktin_load[cid].keys():

                            f.writelines(f'[dpid={sws}\npktin_speed={self.switches_pktin_load[cid][sws]["pktin_speed"]}\npercentage={self.switches_pktin_load[cid][sws]["percentage"]}\n'
                                 
                                  f'pktin_size={self.switches_pktin_load[cid][sws]["pktin_size"]}]\n')

            time.sleep(WRINTE_PKTIN_LOAD_MONITOR)

    def monitor(self):  # 2s打印拓扑
        pass
        '''while True:
           
            time.sleep(MONITOR)'''

def main():

    server=Server()
    server.start()

    accept=Thread(target=server.accept_client)
    accept.start()

if __name__ == '__main__':
    main()