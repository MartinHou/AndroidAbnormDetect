import subprocess
import pandas as pd
import re
import os
import matplotlib.pyplot as plt
import numpy as np
from scipy.fftpack import fft

PKG_NAME = 'EpicLRT'
ROUNDS = 1000


def get_raw_file():
    subprocess.call(
        ['powershell', f'adb shell COLUMNS=512 top -d 1 -H -n {ROUNDS}|grep {PKG_NAME} >{PATH}out1.csv'],
        stdout=subprocess.PIPE)


def make_df(loc):
    with open(loc, 'r', encoding='utf-16') as file:
        da = file.read()
        res_thread = re.findall(r'(?<=:\d{2}.\d{2} ).*(?= com.EpicLRT)', da)
        res_cpu = re.findall(r'(?<= [SR] ) ?\d{1,3}.?\d+', da)
        res_thread = list(map(lambda x: x.strip(), res_thread))
        res_cpu = list(map(float, res_cpu))
        # print(res_thread)
        # print(res_cpu)
        # print(len(res_thread),len(res_cpu))
    df = list(zip(res_thread, res_cpu))
    d = pd.DataFrame(df, columns=['thread', '%CPU'], index=None)
    d.to_csv('out2.csv', index=False)


def analyze(loc):
    df = pd.read_csv(loc)
    name_threads = set(df['thread'])  # 不重复的所有线程名
    count_threads = {thread: 0 for thread in name_threads}  # 线程：目前出现次数
    data_threads = {thread: [0 for _ in range(ROUNDS - 1)] for thread in name_threads}  # 线程：[CPU占用率1 ...]
    max_count = 0  # 当前是第几轮采样（保存字典中出现次数最大值）
    for _, row in df.iterrows():
        name = row['thread']
        cpu = row['%CPU']
        count_threads[name] += 1
        if count_threads[name] > max_count:  # 进入新的采样周期
            max_count += 1
        try:
            data_threads[name][max_count - 1] = cpu
        except IndexError:
            max_count -= 1
            break
    simplified_data = pd.DataFrame(data_threads, index=None)
    simplified_data.to_csv('out3.csv', index=False)
    return max_count


def show_freq(res, n):
    dic = dict()
    for idx, val in res.iteritems():
        # if not thread == 'GameThread':
        #     continue
        thread = val.name
        val = val.values
        res_fft = fft(val)
        abs_y = np.abs(res_fft)[n // 2:]
        normalized_y = abs_y / n
        dic[thread] = list(normalized_y)
    return dic


def get_percentile(nums):
    percentile = 0.995
    nums = sorted(list(nums))
    boundary = round(len(nums) * percentile)
    sum_small, sum_large = sum(nums[:boundary]), sum(nums[boundary:])
    return sum_small, sum_large


def abnormal(dic):
    res = []
    for thread, y in dic.items():
        a, b = get_percentile(y)
        if b <= 0:
            print('数据采样点过少，请扩大采样点')
            break
        elif a / b < 20:  # 最大值与平均值差大于两倍标准差
            res.append((thread, a / b))  # thread出现异常，界定值为a/b
    return res


def deliver_abnormal(ab_res, freq):
    fig, ax = plt.subplots(figsize=(18, 10))
    for thread, num in ab_res:
        x = np.arange(cycles // 2 + 1, cycles + 1)
        ax.scatter(x, freq[thread], s=5, label=thread)
        print(f'{thread} 可能异常，界定值为 {num}')
    plt.legend()
    plt.show()


def show_ori(res, n):
    fig, ax = plt.subplots(figsize=(18, 10))
    x = np.arange(1, n + 1)
    for _, val in res.iteritems():
        name, y = val.name, val.values
        ax.plot(x, y, label=name)
    ax.set_xlabel('采样周期')
    ax.set_ylabel('CPU使用率')
    ax.set_title('各线程CPU使用率随时间变化曲线图')
    ax.legend()
    plt.savefig('out.jpg')
    plt.show()


if __name__ == '__main__':
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False

    cur_PATH = os.path.abspath(__file__)
    PATH = os.path.dirname(cur_PATH) + os.path.sep

    TEST_X20 = 1  # 若测试x20异常数据，则置1
    DO_COLLECT = 0  # 若不重新采集信息，则置零
    if not TEST_X20 and DO_COLLECT:
        get_raw_file()

    if not TEST_X20:
        # 获取了raw的data，若干k行
        make_df('out1.csv')
        # 获取过滤后的raw data
        cycles = analyze('out2.csv')
        result = pd.read_csv('out3.csv')
    else:
        result = pd.read_excel('out3test.xlsx')
        cycles = 722
    # 频域图
    freq_dic = show_freq(result, cycles)  # {thread:[freq...]}

    # 获取异常信息，若异常则打印相关图像和信息
    abnormal_res = abnormal(freq_dic)
    if abnormal_res:
        deliver_abnormal(abnormal_res, freq_dic)
        show_ori(result, cycles)
