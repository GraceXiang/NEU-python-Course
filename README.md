# 东北大学python编程与数据处理课后作业

### v1.0：

* 服务器端加入了多进程实例，开放端口为8080~8084

### 安装：在文件夹根目录下执行 python setup.py install 安装HiCity包

###  导入：在python解释器下执行import HiCity.HiCity as **，导入服务器端模块执行import HiCity.server as **

###  使用(由于客户端和服务端都会阻塞当前进程，因此需要打开两个cmd窗口分别运行)：

* 客户端：执行**.use_interface()，并确保当前文件下存在citycode.txt文件或者City.db，否则数据加载失败，其它功能无法使用。
 
* 服务端：执行**.run_webserver()
