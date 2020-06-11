import numpy as np
import math


# 数据读取
# # #
# # #

# 读取算例文件
def get_data1(file_path):
    '''file_path:算例文件所在路径 '''

    # 打开并逐行读取文件内容到列表lines
    with open(file_path) as file_object:
        lines = file_object.readlines()
    string = ''

    # 寻找BUS DATA FOLLOW开始行，所在行数为bus_r，节点数为bus_n
    bus_r = 0
    bus_n = 0
    for index, value in enumerate(lines):
        string = value[0:16]
        if string == 'BUS DATA FOLLOWS':
            bus_r = index
            number = filter(str.isdigit, lines[bus_r])# 提取这一行的数字
            numbers = ''
            for i in number:
                numbers = numbers + i
            bus_n = int(numbers)# 转化为整型
            break
    # print('the bus data starts at row',bus_r+1,'\n')
    # print('it has',bus_n,'buses','\n')

    # 寻找BRANCH DATA FOLLOW开始行，所在行数为branch_s，支路数输出为branch_n
    branch_s = 0
    branch_n = 0
    for index, value in enumerate(lines):
        string = value[0:19]
        if string == 'BRANCH DATA FOLLOWS':
            branch_s = index
            """提取这一行的数字"""
            number = filter(str.isdigit, lines[branch_s])
            numbers = ''
            for i in number:
                numbers = numbers + i
            branch_n = int(numbers)
            break
    # print('the branch data starts at row',branch_s+1,'\n')
    # print('it has',branch_n,'branches','\n')

    # 读取节点编号(bus_no),节点并联电导(bus_c),节点并联自电纳(bus_s)
    # 节点类型(bus_type),节点电压幅值(bus_voltage)
    # 节点有功负荷(bus_active_load),节点无功负荷(bus_reactive_load),节点发出有功(bus_injected_active),节点发出无功(bus_injected_reactive)
    # 无功出力上限(bus_qmax),无功出力下限(bus_qmin)
    # 功率基准值(basic_S)
    # bus_type值为0或1表示PQ节点，值为2表示PV节点，值为3表示平衡节点
    bus_no = []
    bus_c = []
    bus_s = []
    bus_type = []
    bus_voltage = []
    bus_active_load = []
    bus_generated_active = []
    bus_reactive_load = []
    bus_generated_reactive = []
    bus_qmax = []
    bus_qmin = []
    basic_S = float(lines[0][31:37])
    for i in lines[bus_r + 1:]:
        string = i[0:4]
        if string == '-999':
            break
        else:
            bus_no.append(int(i[0:4].strip()))
            bus_c.append(float(i[106:114].strip()))
            bus_s.append(float(i[114:122].strip()))
            '''若为空字符串，则存为0'''
            if i[24:26] != '  ':
                bus_type.append(int(i[24:26].strip()))
            else:
                bus_type.append(0)
            bus_voltage.append(float(i[27:33].strip()))
            bus_active_load.append(float(i[40:49].strip()) / basic_S)
            bus_generated_active.append(float(i[59:67].strip()) / basic_S)
            bus_reactive_load.append(float(i[49:59].strip()) / basic_S)
            bus_generated_reactive.append(float(i[67:75].strip()) / basic_S)
            bus_qmax.append(float(i[90:98].strip()) / basic_S)
            bus_qmin.append(float(i[98:106].strip()) / basic_S)

    # 把节点并联电导、并联电纳以复数形式整合成节点并联导纳形式，存在bus_y
    bus_y = []
    for i in range(bus_n):
        bus_y.append(complex(bus_c[i], bus_s[i]))
    # print('bus shunt admittance is',bus_y,'\n')

    # 读取支路的开端节点编号(tap_no),末端节点编号(z_no)
    # 互电阻(branch_r),互电抗(branch_x),电纳(line_b),变压器变比(turns_ratio)
    # 支路类型(branch_type)
    tap_no = []
    z_no = []
    branch_r = []
    branch_x = []
    line_b = []
    turns_ratio = []
    branch_type = []
    for i in lines[branch_s + 1:]:
        string = i[0:4]
        if string == '-999':
            break
        else:
            tap_no.append(int(i[0:4].strip()))
            z_no.append(int(i[5:9].strip()))
            '''若为空字符串，则存为0'''
            if i[18] != ' ':
                branch_type.append(int(i[18]))
            else:
                branch_type.append(0)
            branch_r.append(float(i[19:29].strip()))
            branch_x.append(float(i[29:40].strip()))
            line_b.append(complex(0, float(i[40:50].strip())))
            turns_ratio.append(float(i[76:82].strip()))
    # print('tap_no is',tap_no,'\n')
    # print('z_no is', z_no, '\n')
    # print('turns_ratio is', turns_ratio, '\n')
    # print('branch line charging B is', line_b, '\n')

    # 把支路互电阻、互电抗以复数形式整合成互阻抗，存在branch_z
    branch_z = []
    for i in range(branch_n):
        branch_z.append(complex(branch_r[i], branch_x[i]))

    # 把支路互阻抗转换成互导纳，存在branch_y,并设置精度为小数点后8位
    branch_y = []
    for i in range(branch_n):
        branch_admittance = 1 / (branch_z[i])
        real_branch_admittance = branch_admittance.real
        image_branch_admittance = branch_admittance.imag
        real_branch_admittance = float('%.8f' % real_branch_admittance)# 设置精度为小数点后8位
        image_branch_admittance = float('%.8f' % image_branch_admittance)# 设置精度为小数点后8位
        branch_admittance = complex(real_branch_admittance, image_branch_admittance)
        branch_y.append(branch_admittance)
    return bus_n, bus_type, bus_voltage, basic_S, bus_active_load, bus_generated_active, bus_reactive_load, bus_generated_reactive, branch_y, bus_y, tap_no, z_no, branch_type, turns_ratio, line_b

# 读取电压静特性系数
def get_data2(file_path):
    '''file_path:电压静特性文件所在路径，bus_numbers:节点数 '''

    # 打开并逐行读取文件内容到列表lines
    with open(file_path) as file_object:
        lines = file_object.readlines()

    # 读取节点编号(bus_no),常数项系数(ap),一次项系数(bp)
    bus_no = []
    ap = []
    bp = []
    for i in lines:
        bus_no.append(int(i[0:4].strip()))
        ap.append(float(i[5:12].strip()))
        bp.append(float(i[13:22].strip()))
    return bus_no, ap, bp

# 读取耗量特性系数
def get_data3(file_path):
    '''file_path:耗量特性文件所在路径 '''

    # 打开并逐行读取文件内容到列表lines
    with open(file_path) as file_object:
        lines = file_object.readlines()

    # 读取节点编号(bus_no),常数项系数(ap),一次项系数(bp),二次项系数(cp)
    bus_no = []
    ap = []
    bp = []
    cp = []
    for i in lines:
        bus_no.append(int(i[0:4].strip()))
        ap.append(float(i[5:12].strip()))
        bp.append(float(i[13:22].strip()))
        cp.append(float(i[23:33].strip()))
    return bus_no, ap, bp, cp

# 计算PQ、PV节点数量
def node_number(n, type):
    PVn = 0  # 初始化PV节点数量
    for i in range(n):  # n为总节点数
        if type[i] == 2:  # type为节点类型
            PVn += 1
    PQn = n - PVn - 1
    return PVn, PQn
    # print('branch admittance is',branch_y,'\n')


# # #
# # #
# 数据读取over


# 数据保存
# # #
# # #
def save_data(file_path, Ybus, final_Voltage_Amplitude, final_Voltage_Degree, lines_S, final_bus_active,
              final_bus_reactive):
    '''保存节点导纳矩阵'''
    final = '节点导纳矩阵：\n'
    r = np.size(Ybus, 0)# 读取节点导纳矩阵行数
    l = np.size(Ybus, 1)# 读取节点导纳矩阵列数
    for i in range(r):
        a = ''
        for j in range(l):
            a1 = round(Ybus[i][j].real, 4)# 设置精度为小数点后4位
            a2 = round(Ybus[i][j].imag, 4)# 设置精度为小数点后4位
            '''把四舍五入导致的-0.0+0.0j、-0.0-0.0j、0.0-0.0j统一处理成0.0+0.0j'''
            if a2 >= 0:
                t = str(a1) + "+" + str(a2) + "j"
            else:
                t = str(a1) + str(a2) + "j"
            if t == "-0.0+0.0j" or t == "-0.0-0.0j" or t == "0.0-0.0j":
                t = "0.0+0.0j"
            a += t.rjust(30, " ")# 右对齐，每一个数据占30个字符
        final = final + a + '\n'

    '''保存节点电压幅值'''
    final += '\n节点电压幅值: \n'
    for i in range(len(final_Voltage_Amplitude)):
        l = round(final_Voltage_Amplitude[i][0], 3)# 设置精度为小数点后3位
        l = str(l)
        a = l.rjust(30, " ")# 右对齐，每一个数据占30个字符
        final = final + a + '\n'

    '''保存节点电压相角'''
    final += '\n节点电压相角: \n'
    for i in range(len(final_Voltage_Degree)):
        l = round(final_Voltage_Degree[i][0] * 180 / math.pi, 2)# 转换为角度制，并设置精度为小数点后2位
        l = str(l) + '°'
        a = l.rjust(30, " ")# 右对齐，每一个数据占30个字符
        final = final + a + '\n'

    '''保存线路功率'''
    final += '\n线路功率: \n'
    r = np.size(lines_S, 0)# 读取线路功率的行数
    l = np.size(lines_S, 1)# 读取线路功率的列数
    for i in range(r):
        a = ''
        for j in range(l):
            a1 = round(lines_S[i][j].real, 4)# 设置精度为小数点后4位
            a2 = round(lines_S[i][j].imag, 4)# 设置精度为小数点后4位
            '''把四舍五入导致的-0.0+0.0j、-0.0-0.0j、0.0-0.0j统一处理成0.0+0.0j'''
            if a2 >= 0:
                t = str(a1) + "+" + str(a2) + "j"
            else:
                t = str(a1) + str(a2) + "j"
            if t == "-0.0+0.0j" or t == "-0.0-0.0j" or t == "0.0-0.0j":
                t = "0.0+0.0j"
            a += t.rjust(30, " ")# 右对齐，每一个数据占30个字符
        final = final + a + '\n'

    '''保存节点有功'''
    final += '\n节点有功: \n'
    for i in range(len(final_bus_active)):
        l = round(final_bus_active[i][0], 1)# 设置精度为小数点后1位
        l = str(l)
        a = l.rjust(30, " ")# 右对齐，每一个数据占30个字符
        final = final + a + '\n'

    final += '\n节点无功: \n'
    for i in range(len(final_bus_reactive)):
        l = round(final_bus_reactive[i][0], 1)# 设置精度为小数点后1位
        l = str(l)
        a = l.rjust(30, " ")# 右对齐，每一个数据占30个字符
        final = final + a + '\n'

    file_path = file_path + "/final.txt"
    file = open(file_path, 'w', encoding='utf-8')# 设置编码为utf-8
    file.write(final + '\n')
    # file.close

# # #
# # #
# 数据保存over
