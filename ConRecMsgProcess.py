# -*-coding:utf-8-*-
"""
解析消息
"""
import settings
from StreamInfo import InfoProcess
class ConRecMsgProcess(object):
    def __init__(self,controller):
        self.controller=controller
        self.log=InfoProcess()
    def process(self,msg):
        """
        :param msg: 根据msg类型，使用不同方法
        """
        type = msg["msg_type"]

        if type=="set_id":
            self._set_id(msg)
            return

        if type=="flow_mod":
            self._flow_mod(msg)
            return

        if type=="packet_out":
            self._packet_out(msg)
            return

        if type=="flood":
            self._flood(msg)
            return

    """
        消息入口类
    """
    def _set_id(self,msg):
        """
        :param msg: 设置ID的消息体json格式
        """
        self.controller.controller_id=msg["controller_id"]
        self.log.warning(f'{msg["info"]} 服务器分配ID:{self.controller.controller_id}')

    def _flow_mod(self,msg):
        data=msg["data"]
        dpid,ip_src,ip_dst,out_port=data["dpid"],data["ip_src"],data["ip_dst"],data["out_port"]
        priority=settings.CROSSREQUIRE_PRIORITY
        idle_time,hard_time=settings.IDLE_TIME_OUT,settings.HARD_TIME_OUT
        self.controller.handle_flow_mod(dpid,ip_src,ip_dst,out_port,priority,idle_time,hard_time)

    def _packet_out(self,msg):
       """
       :param msg:
       msg=json.dumps({
            "msg_type":"packet_out",
            "data":{
                "paser_id":parser_id,
                "dpid":f,
                "out_port":out_port,
                "msg_data":data
            }
        })
       :return:
       """
       data=msg["data"]
       dst_dpid,out_port,msg_data,buffer_id,in_port=data["dpid"],data["out_port"],data["msg_data"],data["buffer_id"],data["in_port"]
       datapath=self.controller.get_datapath(dst_dpid)
       ofproto = datapath.ofproto

       #self.controller.log.info("Server调用packetout")
       if buffer_id and in_port:
           self.controller.send_packet_out(datapath, buffer_id,
                                           in_port,out_port, self.hexstr_to_bytes(msg_data))
       else:
           self.controller.send_packet_out(datapath,ofproto.OFP_NO_BUFFER,ofproto.OFPP_CONTROLLER,
                                         out_port,self.hexstr_to_bytes(msg_data))

    def _flood(self,msg):
        #self.log.info(f'FLOOD本地area')
        data=msg["data"]
        msg_data=data["msg_data"]
        self.controller.flood_local(self.hexstr_to_bytes(msg_data))



    """
        消息处理类
    """
    @staticmethod
    def hexstr_to_bytes(data):
        """
        :param data: 十六进制字符串
        :return: 将十六进制字符串转为十六进制字节
        """
        return bytes.fromhex(data)