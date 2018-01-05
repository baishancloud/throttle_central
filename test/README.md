## 测试方法

使用[上传脚本](https://coding.net/u/renzhi/p/ops/git/blob/master/src/upload_directory.py)
往指定用户指定bucket中上传文件，该上传脚本支持设置不同的上传速度。

为指定用户设置一个固定的上传带宽限制，然后设置不同的上传速度上传文件，观察
上传过程中实际消耗的带宽，和被拒绝的请求的个数。

实际消耗的带宽和请求被拒绝的个数可以通过中心节点模块提供的monitor接口获取。

## 测试步骤

1，创建测试用户和测试bucket。

2，为用户设置资源限制的配置。

3，为上传脚本配置合理参数，运行脚本上传文件。

4，运行脚本'loop_monitor.py'循环访问monitor接口，获取每秒中，用户实际消耗
    资源的数量，和被拒绝请求的个数。该脚本默认只获取300秒的统计信息，并会
    将结果保存到文件'loop_monitor_report.txt'中。

5，使用'python check_lost_slot.py'检查获取的统计信息是否完整。

6，使用'python get_average.py' 计算每秒消耗资源数量的平均值。

7，使用'python reject_count.py' 统计出现请求被拒绝的slot的个数。
