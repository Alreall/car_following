import random
import matplotlib.pyplot as plt
import numpy as np
import xlwt
import csv
from matplotlib.pyplot import MultipleLocator
plt.rcParams['font.family'] = 'sans-serif' #设置字体格式
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']

# 定义人工驾驶车辆
class Car:
    def _init_(self, length, width):
        self.length = length                # 车长
        self.width = width                  # 车宽

    length = 3
    width = 1.6

    # 静态参数
    S = 2                                  # 最小安全停车间距
    an = 1                                  # 最大加速度
    bn = 2                                  # 舒适减速
    T = 1.5                                 # 安全车头时距
    ty = 0                                  # 车辆类型
    v_max = 33.3                            # 最大速度
    front = None                            # 前车
    back = None                             # 后车
    v = 0                                   # 车辆速度
    x = 0                                   # 车辆位置
    index = 0                               # 车辆索引
    t1 = 0.4                                # 人工驾驶车辆反应时间
    A = 0

    # 更新车间距
    def updateD(self):
        '''
        采用周期边界，如果头车位置大于道路长度自动变成尾车，实际车间距计算方法为前车位置加道路长度减去后车位置
        '''
        if self.x > self.front.x:
            self.D = self.x - self.front.x + self.front.length - Road.length
        else:
            self.D = self.x - self.front.x + self.front.length

    # 获取速度差
    def updatedV(self):
        self.dV = self.v - self.front.v

    # 更新期望跟驰距离
    def updateD_des(self):
        self.updatedV()
        '''
        加入反应时间后最小安全间距可表示为 S = S0 + v * t
        '''
        # self.D_des = self.S + self.v * (self.T+self.t1) + self.v * self.dV / (2 * (self.an * self.bn) ** 0.5)
        self.D_des = self.S + self.v * self.T + self.v * self.dV / (2 * (self.an * self.bn) ** 0.5)
    # 更新加速度
    def updateA(self):
        self.updateD()
        self.updateD_des()
        self.A = self.an * (1 - (self.v / self.v_max) ** 4 - (self.D_des / self.D) ** 2)

    # 更新车速
    def _update_v(self):
        self.updateA()
        self.v = min(self.v+self.A, self.v_max)             # 车辆速度不超过最大速度
        self.v = max(self.v, 0)                             # 车辆速度不小于0

    # 更新位置
    def update_x(self):
        self._update_v()
        self.x = (self.x+self.v) % Road.length              # 采用周期边界

# 定义CAV车辆
class CAV:
    def _init_(self, length, width):
        self.length = length              # 车长
        self.width = width                # 车宽


    length = 3
    width = 1.6

    # 静态参数
    S = 2                               # 最小安全停车间距
    an = 1                              # 最大加速度
    bn = 2                              # 舒适减速度
    T = 1.1                             # 安全车头时距
    ty = 1                              # 车辆类型
    v_max = 33.3                        # 最大速度
    front = None                        # 前车
    back = None                         # 后车
    x = 0                               # 车辆位置
    v = 0                               # 车辆速度
    index = 0                           # 车辆索引
    t2 = 0.2                            # ACC车辆反应时间
    t3 = 0                              # CACC车辆反应时间
    A = 0

    # 更新车间距
    def updateD(self):
        if self.x > self.front.x:
            self.D = self.x - self.front.x + self.front.length - Road.length
        else:
            self.D = self.x - self.front.x + self.front.length

    # 获取速度差
    def updatedV(self):
        self.dV = self.v - self.front.v

    # 更新ACC期望跟驰距离
    def updateD_des(self):
        self.updatedV()
        # self.D_des = self.S + self.v * (self.T+self.t2) + self.v * self.dV / (2 * (self.an * self.bn) ** 0.5)
        self.D_des = self.S + self.v * self.T + self.v * self.dV / (2 * (self.an * self.bn) ** 0.5)
    # 更新CACC期望跟驰距离
    def updateD_de(self):
        self.updatedV()
        self.D_des = self.S + self.v * self.T + self.v * self.dV / (2 * (self.an * self.bn) ** 0.5)
        # self.D_des = self.S + self.v * (self.T + self.t3) + self.v * self.dV / (2 * (self.an * self.bn) ** 0.5)

    # 更新ACC加速度
    def updateac(self):
        self.updateD()
        self.updateD_des()
        self.A = self.an * (1 - (self.v / self.v_max) ** 4 - (self.D_des / self.D) ** 2)

    # 更新CACC加速度
    def updateca(self):
        self.updateD()
        self.updateD_de()
        self.A = 0.1 * self.front.A + self.an * (1 - (self.v / self.v_max) ** 4 - (self.D_des / self.D) ** 2)

    # 更新车速
    def _update_v(self):
        '''
        如果前车是人工驾驶车辆，CAV车辆退化为ACC车辆，否则以CACC车辆行驶
        '''
        if self.front.ty == 1:
            self.updateca()
            self.v = min(self.v + self.A, self.v_max)
            self.v = max(self.v, 0)
        else:
            self.updateac()
            self.v = min(self.v + self.A, self.v_max)
            self.v = max(self.v, 0)

    # 更新位置
    def update_x(self):
        self._update_v()
        self.x = (self.x + self.v) % Road.length


# 设置道路
class Road:
    def _init_(self, motorPercent, length, width,percent):
        self.motorPercent = motorPercent                        # 道路占有率
        self.length = length                                    # 车道长度
        self.width = width                                      # 车道宽度
        self.percent = percent

    motorPercent = 0.9
    length = 4000
    width = 3.5

    # 初始化道路车辆
    def initCars(self):
        # 计算车辆数量
        self.num0fcar = int(self.length * self.motorPercent / 3)
        # 生成车辆
        self.ls = []
        gas = self.length/self.num0fcar         # 车辆均匀分布
        for i in range(self.num0fcar):
            random_num = random.random()
            if random_num < self.percent:
                c = Car()
                # 等间距放置车辆
                c.x = i * gas
                c.v = 15
                c.index = i
            else:
                c = CAV()
                # 等间距放置车辆
                c.x = i * gas
                c.v = 15
                c.index = i
            self.ls.append(c)                   # 将新生成的车辆添加到车辆列表中
            # 新增车辆为上一辆车的前车
            if i > 0:
                c.back = self.ls[self.ls.index(c)-1]
                c.back.front = c
        # 头车的前车是尾车
        self.ls[len(self.ls)-1].front = self.ls[0]
        self.ls[0].back = self.ls[len(self.ls)-1]

    # 运行
    def run(self, time_max):
        # 初始化道路
        self.initCars()
        # 开始仿真
        for time in range(time_max):
            # 车辆位置更新
            for c in self.ls:
                c.update_x()

def get_v():
    timeMax = 4000
    r = Road()
    r.motorPercent = 0.075
    r.percent = 0.6
    r.initCars()
    V = []
    # V2 = []
    time = []
    for t in range(timeMax):
        '''
        产生2s的扰动，头车以-3m/s2的减速度进行减速，其他车辆照常更新
        '''
        if 1200 <= t <= 1201:
            for c in r.ls:
                if c.index == 99:
                    c.v = c.v-3
                    c.x = (c.x+c.v) % r.length
                else:
                    c.update_x()
        elif 1201 < t < 4000:      # 扰动产生以后的时间
            for c in r.ls:
                c.update_x()          # 车队照常更新
                V.append(c.v)         # V表示增加车辆的一个速度
            a = np.max(V)         # a表示取V中的一个最大值
            b = np.min(V)         # b表示取V中的一个最小值
            if abs(a-b) < 0.1:    # 如果极差小于0.1的话，就将该时间添加至时间中
                time.append(t)
            # V2.append(V)
            V = []
        else:
            for c in r.ls:
                c.update_x()
    print(time)
    # print(V2)
get_v()



