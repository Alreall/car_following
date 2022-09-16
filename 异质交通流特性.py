import random
import matplotlib.pyplot as plt
import numpy as np
import xlwt
import csv


# 定义人工驾驶车辆
class Car:
    def _init_(self, length, width):
        self.length = length            # 车长
        self.width = width              # 车宽

    length = 3
    width = 1.6

    # 静态参数
    S = 2                               # 最小安全停车间距
    an = 1                              # 最大加速度
    bn = 2                              # 舒适减速
    B = -3                              # 后车最大减速度
    T = 1.5                             # 安全车头时距
    ty = 0                              # 车辆类型
    v_max = 33.3                        # 最大速度
    front = None                        # 前车
    back = None                         # 后车
    v = 0                               # 车辆速度
    x = 0                               # 车辆位置
    A = 0                               # 车辆加速度


    # 更新车间距
    def updateD(self):
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
        self.D_des = self.S + self.v * self.T + self.v * self.dV / (2 * (self.an * self.bn) ** 0.5)

    # 更新加速度
    def updateA(self):
        self.updateD()
        self.updateD_des()
        self.A = self.an * (1 - (self.v / self.v_max) ** 4 - (self.D_des / self.D) ** 2)

    # 更新车速
    def _update_v(self):
        self.updateA()
        self.v = max(self.v+self.A, 0)

    # 更新位置
    def update_x(self):
        self._update_v()
        self.x = (self.x+self.v) % Road.length

# 定义智能网联车辆
class CAV:
    def _init_(self, length, width):
        self.length = length            # 车长
        self.width = width              # 车宽

    length = 3
    width = 1.6

    # 静态参数
    S = 2                               # 最小安全停车间距
    an = 1                              # 最大加速度
    bn = 2                              # 舒适减速度
    B = -3                              # 后车最大减速度
    v_max = 33.3                        # 最大速度
    tc = 0.6                            # CACC车辆期望车间时距参数
    ta = 1.1                            # ACC车辆期望车间时距参数
    k0 = 1.1
    k1 = 0.23
    k2 = 0.07
    ty = 1                              # 车辆类型
    front = None                        # 前车
    back = None                         # 后车
    x = 0                               # 车辆位置
    v = 0                               # 车辆速度
    A = 0                               # 车辆加速度

    # 更新车间距
    def updateD(self):
        if self.x > self.front.x:
            self.D = self.front.x + Road.length - self.x - self.front.length
        else:
            self.D = self.front.x - self.x - self.front.length

    # 获取速度差
    def updatedV(self):
        self.dV = self.front.v - self.v

    # 更新加速度
    def updateac(self):
        self.updateD()
        self.updatedV()
        self.A = self.k1*(self.D-self.S-self.ta*self.v)+self.k2 * self.dV

    # 更新误差
    def updateca(self):
        self.updateD()
        self.A = self.k0*self.front.A+self.k1*(self.D-self.S-self.tc*self.v)+self.k2 * self.dV

    # 更新车速
    def _update_v(self):
        if self.front.ty == 1:
            self.updateca()
            self.A = min(self.A, self.an)
            self.A = max(self.A, self.B)
            self.v = max(min(self.v+self.A, self.v_max), 0)
        else:
            self.updateac()
            self.A = min(self.A, self.an)
            self.A = max(self.A, self.B)
            self.v = max(min(self.v + self.A, self.v_max), 0)

    # 更新位置
    def update_x(self):
        self._update_v()
        self.x = (self.x + self.v) % Road.length

# 设置道路
class Road:
    def _init_(self, motorPercent, length, width):
        self.motorPercent = motorPercent                        # 道路占有率
        self.length = length                                    # 车道长度
        self.width = width                                      # 车道宽度


    motorPercent = 0.9
    length = 1000
    width = 3.5

    # 初始化道路车辆
    def initCars(self):
        # 计算车辆数量
        self.num0fcar = int(self.length / 3 * self.motorPercent)
        # 生成车辆
        self.ls = []
        gas = self.length/self.num0fcar
        for i in range(self.num0fcar):
            random_num = random.random()
            if random_num < 1:
                c = Car()
                # 等间距放置车辆
                c.x = i * gas
                c.v = 0
                c.index = i
            else:
                c = CAV()
                # 等间距放置车辆
                c.x = i * gas
                c.v = 0
                c.index = i
            self.ls.append(c)
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

# 获取输入道路的平均车速
def get_vMean(r, timeMax):
    # 初始化道路
    r.initCars()
    # 开始仿真
    ls = []
    vSum = 0
    for time in range(timeMax):
        # 车辆位置更新
        for c in r.ls:
            c.update_x()
            vSum = vSum + c.v
        # 计算当前时间步平均车速
        ls.append(vSum / r.num0fcar)
        vSum = 0
    return sum(ls) / len(ls)

# 获取密度-速度
def get_K_V():
    V_ls = np.zeros((1, 50))
    K_ls = np.zeros((1, 50))
    timeMax = 1000
    j = 0
    for i in np.arange(0.02, 1, 0.02):
        r = Road()
        r.motorPercent = i
        V_ls[0, j] = get_vMean(r, timeMax)*1.8
        K_ls[0, j] = r.num0fcar / r.length * 2000
        j = j + 1
    return K_ls, V_ls

# 绘制速度-密度图
def plot_K_V(K_V):
    # 输入元组第0个元素为密度，第1个元素为平均速度
    ls_K = []
    ls_V = []
    for i in range(19):
        ls_K.append(K_V[0][0, i])
        ls_V.append(K_V[1][0, i])
    plt.plot(ls_K, ls_V)
    plt.title('密度-速度图', fontsize=35)
    plt.xlabel('密度', fontsize=30)
    plt.ylabel('速度', fontsize=30)
    plt.xticks(fontsize=20)
    plt.yticks(fontsize=20)
    plt.show()

# 绘制流量-密度图
def plot_K_Q(K_V):
    # 输入元组第0个元素为密度，第1个元素为平均速度
    ls_K = []
    ls_Q = []
    for i in range(49):
        ls_K.append(K_V[0][0, i])
        ls_Q.append(K_V[1][0, i] * K_V[0][0, i])
    plt.plot(ls_K, ls_Q)
    plt.title('密度-流量图', fontsize=35)
    plt.xlabel('密度', fontsize=30)
    plt.ylabel('流量', fontsize=30)
    plt.xticks(fontsize=20)
    plt.yticks(fontsize=20)
    plt.show()

# 绘制流量-速度图
def plot_V_Q(K_V):
    # 输入元组第0个元素为密度，第1个元素为平均速度
    ls_V = []
    ls_Q = []
    for i in range(19):
        ls_V.append(K_V[1][0, i])
        ls_Q.append(K_V[1][0, i] * K_V[0][0, i])
    plt.plot(ls_Q, ls_V)
    plt.title('速度-流量图', fontsize=35)
    plt.xlabel('流量', fontsize=30)
    plt.ylabel('速度', fontsize=30)
    plt.xticks(fontsize=20)
    plt.yticks(fontsize=20)
    plt.show()


# def xlsWrite(K_V):
#     workbook = xlwt.Workbook(encoding='ascii')
#     worksheet = workbook.add_sheet("三参数")
#     worksheet.write(0, 0, "密度")
#     worksheet.write(0, 1, "速度")
#     worksheet.write(0, 2, "流量")
#     for i in range(20):
#         worksheet.write(i + 1, 0, K_V[0][0, i])
#         worksheet.write(i + 1, 1, K_V[1][0, i])
#         worksheet.write(i + 1, 2, K_V[0][0, i] * K_V[1][0, i])
#     fname = "10.xls"
#     workbook.save(fname)

def xlsWrite(K_V):
    # 创建文件对象
    f = open('p=0.csv','w',encoding='utf-8',newline="")
    # 基于文件对象构建csv写入对象
    csv_write = csv.writer(f)
    # 构建列表头
    csv_write.writerow(['密度', '速度', '流量'])
    # 写入csv文件
    for i in range(50):
        csv_write.writerow([K_V[0][0, i],K_V[1][0, i],K_V[0][0, i] * K_V[1][0, i]])
    f.close()

#################### main
# 创建道路
r = Road()
# 展示动画
################### 动画展示
r.motorPercent = 0.3
timeMax = 100
# r.show(timeMax)
################### 三参数图
# 获取占有率-速度
K_V = get_K_V()
# 汇出密度-速度图
# plot_K_V(K_V)
# 汇出密度-流量图
# plot_K_Q(K_V)
# 汇出速度-流量图
################### 导出数据
# plot_V_Q(K_V)
# 写入excel文件
xlsWrite(K_V)
# generate_data(K_V)
################### V0变化
# for i in range(1,7):
#     Car.V0 = 5*i
#     K_V = get_K_V()
#     plot_K_Q(K_V)
#     #plot_V_Q(K_V)
#     #plot_K_V(K_V)
# plt.legend(labels=['5','10','15','20','25','30'],fontsize = 20)
################### S变化
# for i in range(1,6):
#     Car.S = i
#     K_V = get_K_V()
#     #plot_K_Q(K_V)
#     #plot_V_Q(K_V)
#     plot_K_V(K_V)
# plt.legend(labels=['1','2','3','4','5'],fontsize = 20)
################### par变化
# for i in range(1,6):
#     Car.par = i*0.2
#     K_V = get_K_V()
#     plot_K_Q(K_V)
#     #plot_V_Q(K_V)
#     #plot_K_V(K_V)
# plt.legend(labels=['0.2','0.4','0.6','0.8','1'],fontsize = 20)

