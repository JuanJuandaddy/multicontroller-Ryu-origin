option= {
    "title": {"text": "集群负载状况"},
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross", "label": {"backgroundColor": "#6a7985"}},
    },
    "legend": {"data": ["总PacketIn负载  pkts/s", "平均响应时延迟  us(微秒)"]},
    "toolbox": {"feature": {"saveAsImage": {}}},
    "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
    "xAxis": [
        {
            "type": "category",
            "boundaryGap": False,
            "data": ["控制器C1", "控制器C2", "控制器C3", "控制器C4", "控制器C5"],
        }
    ],
    "yAxis": [{"type": "value"}],
    "series": [

        {
            "name": "总PacketIn负载  pkts/s",
            "type": "line",
            "stack": "总量",
            "areaStyle": {},
            "label": {"show": True, "position": "top"},
            "emphasis": {"focus": "series"},
            "data": [120, 132, 101, 134, 90, 230, 210],
        },
        {
            "name": "平均响应时延迟  us(微秒)",
            "type": "line",
            "stack": "总量",
            "areaStyle": {},
            "label": {"show": True, "position": "top"},
            "emphasis": {"focus": "series"},
            "data": [220, 182, 191, 234, 290, 330, 310],
        }
    ],
}
