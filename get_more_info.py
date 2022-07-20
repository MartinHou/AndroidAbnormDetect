import re
import subprocess
import pandas as pd

PKG_NAME = 'com.EpicLRT.ActionRPGSample'
REPORT_PREFIX = 'python simpleperf/report.py '
TIME = 30


def strip_top(file_loc):
    with open(file_loc, 'r', encoding='utf-16') as file:
        dso = file.read()
    with open(file_loc, 'w', encoding='utf-16') as file:
        dso = re.search(r'Overhead[\d\D]*', dso).group()
        file.write(dso)


def main():
    """
    进行一次监控，获取perf文件
    """
    monitor_on = 1  # 不采集则置零
    if monitor_on:
        subprocess.call(['powershell', 'python ./simpleperf/app_profiler.py -p ' + PKG_NAME + f' -r "--duration {TIME}"'],
                        stdout=subprocess.PIPE)

    '''
    最耗时线程
    '''
    subprocess.call(['powershell', REPORT_PREFIX + ' --sort tid,comm --csv >.\\cache\\out_thread.txt'])
    strip_top('./cache/out_thread.txt')
    res_thread = pd.read_csv('./cache/out_thread.txt', encoding='utf-16', sep=',')
    costliest_tid = res_thread.iloc[0, 1]  # 最耗时线程号
    thread_time = res_thread.iloc[0, 0]  # 耗时
    command = res_thread.iloc[0, 2]
    print(
        f'The costliest thread is {command}, whose TID is {costliest_tid}\nIt accounted for {thread_time} of the time')

    '''
    共享库耗时排行表（.so）
    '''
    subprocess.call(['powershell', REPORT_PREFIX + '--sort dso --csv >.\\cache\\out_dso.txt'])
    strip_top('./cache/out_dso.txt')
    res_dso = pd.read_csv('./cache/out_dso.txt', encoding='utf-16', sep=',')
    costliest_dso = res_dso.iloc[0, 1]  # 最耗时共享库名
    dso_time = res_dso.iloc[0, 0]  # 耗时
    print(f'The costliest .so is {costliest_dso}\nIt accounted for {dso_time} of the time')

    '''
    最耗时共享库中的函数耗时排行表
    '''
    subprocess.call(['powershell', REPORT_PREFIX + '--dsos ' + costliest_dso + ' --csv --sort symbol '
                                                                               '>.\\cache\\out_symbol.txt'])
    strip_top('./cache/out_symbol.txt')
    res_func = pd.read_csv('./cache/out_symbol.txt', encoding='utf-16', sep=',')
    costliest_func = res_func.iloc[0, 1]  # 最耗时函数原型
    func_time = res_func.iloc[0, 0]  # 耗时
    print(f'The costliest function is {costliest_func}\nIt accounted for {func_time} of the time')

    '''
    判断异常
    '''
    if eval(dso_time[:-1]) > 70:
        print('========最大耗时共享库耗时占比过大===========')
    elif eval(func_time[:-1]) > 10:
        print('========最大耗时共享库的最大耗时函数耗时过长==========')
    elif eval(thread_time[:-1]) > 70:
        print('=========最大线程耗时占比过大===========')


if __name__ == '__main__':
    main()
