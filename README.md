# multicontroller-Ryu-origin
## 通过./start脚本启动，此脚本会开出7个终端（分别是5个控制器端、一个Server端、一个拓扑端），请确保虚拟机有足够的性能

## 跨域ping前，请先确保ping的主机对已经被ping过。

## 比如h10 h11  , h30 h31 四个主机处于不同的通信域，在h10 ping h30之前，请先使用h10 ping h11 ,h30 ping h31，让控制器arp一下，随后就可以h10 ping h30了

## 相关参数说明在settings文件中，以及跨域通信逻辑请自行阅读源码



