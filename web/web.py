import sys

import re

import subprocess

import time
import pandas as pd
import numpy as np
import os
sys.path.append("..")
from echarts import total_option,div_option,topo_option
import streamlit as st
from selenium import webdriver
from PIL import Image
from echarts import toecharts
from streamlit_autorefresh import st_autorefresh
controllers_num=5
from streamlit_echarts import st_pyecharts, st_echarts

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

                columns=st.columns(controllers_num)

                for col in columns:

                    with col:
                        st_echarts(options=div_option.option,height="400px",key=f'{col.__str__()}')



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
    MainBar(1)