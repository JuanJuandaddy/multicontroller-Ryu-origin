# -*-coding:utf-8-*-
# -*-this is a python script -*-
import re

import subprocess

import time
import pandas as pd
import numpy as np
import os
from echarts import total_option,div_option,topo_option
import streamlit as st
from selenium import webdriver
from PIL import Image
from echarts import toecharts
from streamlit_autorefresh import st_autorefresh
controllers_num=0
from streamlit_echarts import st_pyecharts, st_echarts
def template(name, value):
    if type(value)==str :
        return f'{name}=\'{value}\'\n'
    else:
        return f'{name}={value}\n'

class SideBar(object):

    def __init__(self,name):
        self.name=st.sidebar.title(name)

        server,socket,controller,topo,experiment,pingall,file_storage,role,mac=st.sidebar.tabs(["服务器","Socket","控制器","拓扑",
                                                                      "实验","初始化","文件","角色","MAC",])

        with server:
            st.subheader("服务器配置")

            self.MsgBarrier=st.text_input(label="JSON消息分隔符(避免Socket乱序)",value="/")

            self.IP = st.selectbox('Server监听IP地址',('192.168.10.3', '127.0.0.1'))

            self.PORT=st.number_input("Server监听端口",value=8888)

            self.QUEUE_LEN = st.number_input("队列长度",value=500,step=100)

            self.CONTROLLER_NUM = st.number_input("控制器数量",value=5)

            self.WAIT_CONNECT = st.number_input("最大等待连接数",value=10,min_value=10) # 最大等待连接数

            self.WRINTE_PKTIN_LOAD_MONITOR = st.number_input("获取pktin负载的周期",value=5,min_value=2,max_value=10,step=1)  # 获取pktin负载的周期

        with socket:
            st.subheader("套接字配置")

            self.SERVER_RECV_BUFSIZE =st.number_input(label="服务器接受缓冲区大小 单位/bytes",value=204800000,step=102400000,min_value=102400000)

            self.CLIENT_RECV_BUFSIZE =st.number_input(label="控制器接受缓冲区的大小 单位/bytes",value=204800000,step=102400000,min_value=102400000)

        with role:
            st.subheader("Role映射配置(勿改)")
            self.ID_ROLE_MAP={
                            0:"NOCHANGE",
                            1:"EQUAL",
                            2:"MASTER",
                            3:"SLAVE"
                        }
            st.text_area(label="默认OpenFlow映射",value=self.ID_ROLE_MAP,label_visibility="collapsed")

        with controller:
            st.subheader("控制器配置,流表都不过期")

            self.CONTROLLER_PKT_THRESHOLD= st.number_input(label="控制器PKTIN最大处理能力pkts/s",value=1600)

            self.ECHO = st.number_input("控制器监控周期",value=5)  # 单位秒

            self.CONTROLLER_IP = st.selectbox('控制器IP',('127.0.0.1','192.168.10.3'))  # 控制器的IP

            self.OFP_VERSION = st.selectbox('OpenFlow版本',('OpenFlow13', 'OpenFlow14','OpenFlow15','OpenFlow10','OpenFlow12'))  # openflow版本

            self.ECHO_DELAY = st.number_input("几个周期后开始request",value=1,min_value=1)  # 几个周期后开始request

            self.PERFORMANCE_STATISTIC_ECHO = st.number_input("获取交换机性能的间隔",value=5)  # 打印交换机平均响应时延的间隔

            self.SW_TO_SW_PRIORITY = st.selectbox('域内交换机之间的流表传输优先级',(30,20,10,40,50,60)) # 交换机之间的流表传输优先级

            self.IPV6_PRIORITY = st.number_input("IPV6表项的优先级" ,min_value=65534,max_value=65534 ) # IPV6表项的优先级

            self.SW_TO_HOST_PRIORITY = st.selectbox('接入层流表的优先级',(50,20,10,40,30,60))  # 接入层流表的优先级

            self.TABLEMISS_PRIORITY = st.number_input("table-miss的优先级" ,min_value=0,max_value=0 )  # table-miss的优先级

            self.CROSSREQUIRE_PRIORITY = st.selectbox('跨域请求的流表优先级',(30,20,10,40,50,60))  # 跨域请求的流表优先级

            self.IDLE_TIME_OUT = st.selectbox('空闲过期时间  跨域与非跨域过期时间相同',(0,20,10,40,50,60,30))  # 空闲过期时间  跨域与非跨域过期时间相同

            self.HARD_TIME_OUT = st.selectbox('绝对过期时间  跨域与非跨域过期时间相同',(0,20,10,40,50,60,30))  # 绝对过期时间  跨域与非跨域过期时间相同

        with topo:
            # TOPO
            st.subheader("拓扑配置(不用动)")

            self.TOPO=st.selectbox('拓扑样式',("OS3E",))

            # 控制器ID，代表有子网0和子网1，代表着有area0和area1两个控制area，
            # 在Ryu源码中该配置极其重要，务必2者保持一致
            self.CONTROLLERS = st.multiselect(label="控制器节点(OS3E默认配置)",options=['c'+str(num) for num in range(0,10)],default=['c0', 'c1', 'c2', 'c3', 'c4'])

            self.CONTROLLER_PORTS = st.multiselect(label="控制器监听端口(OS3E默认配置)",options=[port for port in range(6650,6659)] ,default=[6653, 6654, 6655, 6656, 6657] ) # 控制器端口

            self.WAITING_FOR_STABLE_NETWORK_SECONDS = st.number_input("网络稳定等待时长 单位秒" ,value=10,min_value=5 )

            self.EACH_SW_HOSTS_NUM = st.number_input("每个交换机下所连接的主机数量", value=3)




            # 链路连接信息，端口可以不指定，如果需要指定链接的端口，前往os3e拓扑文件中的create——link方法中，使用port信息
            self.EDGE_LINK = {("s13", "s33"): [3, 2], ("s15", "s31"): [5, 2], ("s16", "s21"): [4, 2]
                , ("s22", "s31"): [2, 4], ("s23", "s32"): [2, 2], ("s24", "s51"): [3, 2],
                         ("s26", "s55"): [3, 2], ("s33", "s43"): [3, 2], ("s34", "s52"): [3, 2],
                         ("s54", "s40"): [3, 2]}  # 边缘交换机的连接端口，用于Server对全局拓扑的初始化

            self.SW_LINK = {("s10", "s11"): [2, 2], ("s10", "s13"): [5, 2], ("s10", "s15"): [4, 2], ("s10", "s12"): [3, 2],
                       ("s12", "s14"): [3, 2], ("s14", "s15"): [3, 3], ("s14", "s16"): [4, 2], ("s16", "s15"): [3, 4],
                       ("s21", "s20"): [3, 2], ("s20", "s22"): [3, 3], ("s31", "s32"): [3, 3], ("s20", "s25"): [4, 2],
                       ("s23", "s25"): [3, 3], ("s32", "s30"): [4, 3], ("s30", "s33"): [2, 4], ("s25", "s24"): [4, 2],
                       ("s25", "s26"): [5, 2], ("s30", "s34"): [4, 2], ("s52", "s53"): [3, 2], ("s51", "s53"): [3, 3],
                       ("s53", "s50"): [4, 2], ("s50", "s55"): [4, 3], ("s55", "s56"): [4, 2], ("s50", "s54"): [3, 2],
                       ("s40", "s41"): [3, 2], ("s41", "s42"): [3, 2], ("s42", "s43"): [3, 3], ("s43", "s44"): [4, 2],
                       ("s44", "s45"): [3, 2], ("s45", "s46"): [3, 2], ("s46", "s47"): [3, 2], ("s47", "s40"): [3, 4]}
            # 交换机之间的链路

            # get map
            def get_map(LINKS):
                PREPARE = ["s" + str(i) for i in range(10, 60)]
                ALL = PREPARE.copy()
                for k in LINKS.keys():

                    if k[0] in PREPARE:
                        PREPARE.remove(k[0])
                    if k[1] in PREPARE:
                        PREPARE.remove(k[1])
                for h in PREPARE:
                    ALL.remove(h)

                HOSTS = {}
                SW_LIST = [[] for _ in range(5)] #5个控制器
                HOST_LIST = [[] for _ in range(5)]

                def h(x):
                    #3 台主机
                    return x, ["h" + x.split("s")[1]+'01',"h" + x.split("s")[1]+'02',"h" + x.split("s")[1]+'03']

                for host in map(h, ALL):
                    HOSTS[host[0]] = host[1]

                for c in ALL:
                    SW_LIST[int(list(c)[1]) - 1].append(c)
                    # 3 台主机
                    HOST_LIST[int(list(c)[1]) - 1].append(["h" + c.split("s")[1]+'01',"h" + c.split("s")[1]+'02',"h" + c.split("s")[1]+'03'])


                return HOSTS, SW_LIST, HOST_LIST

            self.SW_HOST, self.SWS, self.HOSTS = get_map(self.SW_LINK)
            # SW_HOST 交换机与主机之间的映射
            # SWS  全体交换机，区分控制器
            # HOSTS 全体主机，区分控制器

        with mac:
            # MAC
            st.subheader("MAC配置".center(30))
            self.UNKNOWN_MAC = st.text_input(label="ARP请求的IP中默认的未知MAC(勿改)",value="00:00:00:00:00:00") # ARP请求的IP中默认的未知MAC

            self.BROADCAST_MAC = st.text_input(label="广播地址(勿改)",value="ff:ff:ff:ff:ff:ff")# 广播地址

        with pingall:
            # PingAll Parameters 默认采取PING  非HPING3
            st.subheader("网络初始化通信配置(PING)".center(30))
            self.PING_NUM = st.number_input("每个主机发送x个ping包来实现基础网络互通" ,min_value=5)  # 每个主机发送 x 个ping包来实现基础网络互通

            self.PING_INTERVAL = st.number_input("每对主机之间的间隔时间 单位秒" ,value=0.5,min_value=0.0,step=0.1,max_value=2.0)  # 每对主机之间的间隔时间 单位秒

            self.PING_OUT_MODE = st.selectbox('是否域外ping 1 开 || 0 不开 || 此步较为耗时 默认不开',(0,1))  # 是否域外ping ，1 is 开 || 0 is 不开

            self.PING_IN_OUT_INTERVAL = st.number_input("开启域外ping之后，此选项才有效,域内和域外ping的时间间隔 单位秒" ,min_value=3)   # 开启域外ping之后，此选项才有效。域内和域外ping的时间间隔 单位秒

        with experiment:
            # Packet_In Parameters  默认采取HPING3  非PING
            st.subheader("实验配置".center(30))

            pkt_stress,topo_stress=st.tabs(["PKTIN压力配置","PKTIN交换机压力配置"])

            with topo_stress:

                c1, c2, c3, c4, c5 = st.tabs(["控制器：C" + str(i + 1) for i in range(5)])
                with c1:


                    self.C1_LOAD_RATE=st.number_input(label="过载率",value=0.75,min_value=0.1,max_value=0.8,step=0.05,key='C1_OVERLOAD_RATE')
                with c2:

                    self.C2_LOAD_RATE=st.number_input(label="过载率",value=0.75,min_value=0.1,max_value=0.8,step=0.05,key='C2_OVERLOAD_RATE')

                with c3:

                    self.C3_LOAD_RATE=st.number_input(label="过载率",value=0.75,min_value=0.1,max_value=0.8,step=0.05,key='C3_OVERLOAD_RATE')

                with c4:

                    self.C4_LOAD_RATE=st.number_input(label="过载率",value=0.75,min_value=0.1,max_value=0.8,step=0.05,key='C4_OVERLOAD_RATE')

                with c5:

                    self.C5_LOAD_RATE=st.number_input(label="过载率",value=0.75,min_value=0.1,max_value=0.8,step=0.05,key='C5_OVERLOAD_RATE')

        with file_storage:

            global controllers_num

            st.subheader("文件存储，控制器各个指标的存储位置(不可更改)".center(30))

            root_dir="/home/ryu/multicontroller/zoomulti"

            cnums=len(self.CONTROLLERS)

            controllers_num=cnums

            cons = self.CONTROLLERS

            speed_delay,global_config,experiment_config=st.tabs(["PKT性能配置文件","全局配置文件","实验配置文件"])

            with speed_delay:

                performance_class='speed_delay'

                for i in range(cnums):

                    con=cons[i]

                    sequence=re.findall('\d',con)

                    st.text_input(label=f'控制器编号 {con}', placeholder=f'{root_dir}/{performance_class}/controller_{int(sequence[0])+1}_pktspeed_delay')
            with global_config:
                st.text_input(label="全局控制文件地址",placeholder=f'{root_dir}/settings.py')
            with experiment_config:
                st.text_input(label="实验配置文件地址",placeholder=f'{root_dir}/exp_conf.py')

        self.button=st.sidebar.button(label="提交配置",use_container_width=True,type="primary",on_click=self.start)

        st.header("===============性能展示==============")

        st.button(label="运行实例", type="primary", use_container_width=True, on_click=self.run)

        st.button(label="清除实例", type="primary", use_container_width=True, on_click=self.cancel)

    def start(self):
        try:
            with open("/home/ryu/multicontroller/zoomulti/settings.py",'w+') as f:
                f.writelines("#-*-集群部署配置文件-*-\n")
                f.writelines(template("MsgBarrier",self.MsgBarrier))
                f.writelines(template("PORT",self.PORT))
                f.writelines(template("IP", self.IP))
                f.writelines(template("QUEUE_LEN", self.QUEUE_LEN))
                f.writelines(template("CONTROLLER_NUM", self.CONTROLLER_NUM))
                f.writelines(template("SERVER_RECV_BUFSIZE", self.SERVER_RECV_BUFSIZE))
                f.writelines(template("CLIENT_RECV_BUFSIZE", self.CLIENT_RECV_BUFSIZE))
                f.writelines(template("ID_ROLE_MAP", self.ID_ROLE_MAP))
                f.writelines(template("ECHO", self.ECHO))
                f.writelines(template("CONTROLLER_IP", self.CONTROLLER_IP))
                f.writelines(template("OFP_VERSION", self.OFP_VERSION))
                f.writelines(template("ECHO_DELAY", self.ECHO_DELAY))
                f.writelines(template("PERFORMANCE_STATISTIC_ECHO",self.PERFORMANCE_STATISTIC_ECHO))
                f.writelines(template("SW_TO_SW_PRIORITY", self.SW_TO_SW_PRIORITY))
                f.writelines(template("IPV6_PRIORITY", self.IPV6_PRIORITY))
                f.writelines(template("SW_TO_HOST_PRIORITY", self.SW_TO_HOST_PRIORITY))
                f.writelines(template("TABLEMISS_PRIORITY", self.TABLEMISS_PRIORITY))
                f.writelines(template("CROSSREQUIRE_PRIORITY", self.CROSSREQUIRE_PRIORITY))
                f.writelines(template("IDLE_TIME_OUT", self.IDLE_TIME_OUT))
                f.writelines(template("HARD_TIME_OUT", self.HARD_TIME_OUT))
                f.writelines(template("WAIT_CONNECT", self.WAIT_CONNECT))
                f.writelines(template("WRINTE_PKTIN_LOAD_MONITOR", self.WRINTE_PKTIN_LOAD_MONITOR))
                f.writelines(template("CONTROLLERS", self.CONTROLLERS))
                f.writelines(template("CONTROLLER_PORTS", self.CONTROLLER_PORTS))
                f.writelines(template("WAITING_FOR_STABLE_NETWORK_SECONDS", self.WAITING_FOR_STABLE_NETWORK_SECONDS))
                f.writelines(template("EDGE_LINK", self.EDGE_LINK))
                f.writelines(template("SW_LINK", self.SW_LINK))
                f.writelines(template("SW_HOST", self.SW_HOST))
                f.writelines(template("SWS", self.SWS))
                f.writelines(template("HOSTS", self.HOSTS))
                f.writelines(template("PING_NUM", self.PING_NUM))
                f.writelines(template("PING_INTERVAL", self.PING_INTERVAL))
                f.writelines(template("PING_OUT_MODE", self.PING_OUT_MODE))
                f.writelines(template("PING_IN_OUT_INTERVAL", self.PING_IN_OUT_INTERVAL))
                f.writelines(template("UNKNOWN_MAC", self.UNKNOWN_MAC))
                f.writelines(template("BROADCAST_MAC", self.BROADCAST_MAC))
                f.writelines(template("CONTROLLER_PKT_THRESHOLD",self.CONTROLLER_PKT_THRESHOLD))
                f.writelines(template("EACH_SW_HOSTS_NUM",self.EACH_SW_HOSTS_NUM))

            with open("/home/ryu/multicontroller/zoomulti/exp_conf.py","w+") as f:
                f.writelines(template("CONTROLLER_OVERLOAD",{"C1":{"RATE":self.C1_LOAD_RATE},
                                                             "C2":{"RATE":self.C2_LOAD_RATE},
                                                             "C3":{"RATE":self.C3_LOAD_RATE},
                                                             "C4":{"RATE":self.C4_LOAD_RATE},
                                                             "C5":{"RATE":self.C5_LOAD_RATE}}))

        except Exception as e:
            st.caption(f'当前时间{time.ctime()}')
            st.caption(f'本次配置提交状态：:red[提交失败]')
            raise e
        else:
            st.caption(f'当前时间{time.ctime()}')
            st.caption(f'本次配置提交状态：:red[成功]')

    def run(self):
        try:
            #先保存配置
            self.start()

            subprocess.Popen("/home/ryu/multicontroller/zoomulti/start",shell=True)
        except Exception as e:
            raise e

    def cancel(self):
        try:
            os.system(f'kp {self.PORT}')
        except Exception as e:
            raise e
        else:
            st.caption(f':red[清除成功]')

class MainBar(object):
    def __init__(self,refresh_time):

        self.refresh_time=refresh_time

        self.divide_part()

    def topo_image(self):

        st.image(Image.open('/home/ryu/multicontroller/zoomulti/topo_img/OS3E.jpg'),caption="OS3E拓扑",use_column_width="auto")

    def divide_part(self):

        global  controllers_num

        a1,a2,a3=st.columns(3)

        with st.container():

            self.topo_image()


        with st.container():

            st.subheader("控制器集群性能参数展现形式")

            graph,table=st.tabs(["图表形式","表格形式"])

            with graph:

                st.subheader("控制器集群(图表)")


                total_op=total_option.option

                div_op=div_option.option


                st_echarts(options=total_op,height="400px",key="total")


                st_echarts(options=div_option.option,height="400px",key=f'div')


            with table:
                st.subheader("控制器集群(表格)")

                cs=[]

                for i in range(controllers_num):

                    cs.append(f'控制器：{i+1}')

                ctabs=st.tabs(cs)

                st_autorefresh(2000,key="table")

                for i in range(len(cs)):

                    with ctabs[i]:

                        with open(f"/home/ryu/multicontroller/zoomulti/performance/speed_delay/controller_{i + 1}", "r+") as f:
                            content = f.read()

                            sw_load = {}

                            cid = re.findall('cid=\d*', content)[0].split('=')[1]

                            total_pkt_speed = re.findall('total_pkt_speed=\d*\D\d*', content)[0].split('=')[1]

                            total_pkt_delay = re.findall('total_pkt_delay=\d*\D\d*', content)[0].split('=')[1]

                            st.metric(label="总体控制器PacketIn速率：", value=f'{total_pkt_speed} 个PacketIn包/每秒', delta="s")

                            st.metric(label="平均周期PacketIn响应时延", value=f'{total_pkt_delay} 毫秒', delta='ms')

                            for infomation in re.findall(
                                    '\[dpid=\d*\spktin_speed=\d*\D\d*\spercentage=\d*\D\d*%\spktin_size=\d*\D\d*\]', content):
                                sw_load[re.findall('\d+', infomation.split("\n")[0].replace("[", ""))[0]] = [
                                    re.findall('\d+\D\d+', infomation.split("\n")[1])[0] + " 个/s",
                                    re.findall('\d+\D\d+', infomation.split("\n")[2])[0] + " %",
                                    re.findall('\d+\D\d+', infomation.split("\n")[3].replace("]", ""))[0] + " Bytes/s"
                                ]

                            sorted_sw_load = sorted(sw_load.items(), key=lambda x: x[0])

                        df = pd.DataFrame(data=[para[1] for para in sorted_sw_load],
                                          columns=["交换机PacketIn速率", "百分占比", "PacketIn包大小"],
                                          index=["OVS: " + info[0] for info in sorted_sw_load])
                        st.table(df)



if __name__ == '__main__':
    SideBar("集群基础信息配置")
    MainBar(1)