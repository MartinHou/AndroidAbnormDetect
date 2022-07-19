import subprocess
import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np
from scipy.fftpack import fft

PKG_NAME = 'EpicLRT'
ROUNDS = 1000


def get_raw_file():
    subprocess.call(
        ['powershell', f'adb shell COLUMNS=512 top -d 1 -H -n {ROUNDS}|grep {PKG_NAME} >E:\\MyWork\\task2\\out1.csv'],
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
    return d


def analyze(df):
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
        # print(max_count)
        try:
            data_threads[name][max_count - 1] = cpu
        except IndexError:
            max_count -= 1
            break
    # print(data_threads)
    return max_count, data_threads


def show_freq(res, n):
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(n // 2 + 1, n + 1)
    dic = dict()
    for thread, val in res.items():
        # if not thread == 'GameThread':
        #     continue
        res_fft = fft(val)
        abs_y = np.abs(res_fft)[n // 2:]
        normalized_y = abs_y / n
        dic[thread] = list(normalized_y)
        ax.scatter(x, normalized_y, s=5, label=thread)
    plt.legend()
    plt.show()
    return dic


def get_percentile(nums):
    percentile = 0.995
    nums = sorted(list(nums))
    # print(len(nums))
    boundary = round(len(nums) * percentile)
    sum_small, sum_large = sum(nums[:boundary]), sum(nums[boundary:])
    return sum_small, sum_large


def abnormal(dic):
    for thread, y in dic.items():
        a, b = get_percentile(y)
        # print(label,a,b,a/b)
        if b <= 0:
            print('数据采样点过少，请扩大采样点')
            break
        elif a / b < 20:  # 最大值与平均值差大于两倍标准差
            print(f'{thread}可能出现异常! 界定值为:{a / b}')


def show(res, n):
    fig, ax = plt.subplots(figsize=(18, 10))
    x = np.arange(1, n + 1)
    for name, y in res.items():
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

    DO_COLLECT = 0  # 若不重新采集信息，则置零
    if DO_COLLECT:
        get_raw_file()

    # 获取了raw的data，若干k行
    data = make_df('out1.csv')

    # 获取过滤后的raw data
    cycles, result = analyze(data)

    # 获取各线程每个时刻的data
    simplified_data=pd.DataFrame(result,index=None)
    simplified_data.to_csv('out3.csv',index=False)

    freq_dic = show_freq(result, cycles)
    abnormal(freq_dic)
    show(result, cycles)
