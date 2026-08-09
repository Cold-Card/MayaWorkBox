# -*- coding: utf 8 -*-

def getMainLst(lst, interval_num=2, index=False):
    u'''
    传入一个列表，设置间隔数量
    该函数就会从列表索引为0开始，每中间隔两个，就将对应的列表元素放入到新的列表中
    如果 index 为 True ，那么返回的列表内容就是索引值
    这是为了获取蛇类身体ik主控制器列表
    由于这个函数不需要依靠maya的任何命令，所以我将它放在这里
    '''
    value = interval_num + 1
    main_lst = []
    n = 0
    while True:
        if n >= len(lst):
            break
        else:
            if index == False:
                main_lst.append(lst[n])
            else:
                main_lst.append(n)
        n += value
    return main_lst

def equalString(lst):
    u'''
    返回一个链式相等的字符串
    例：
        lst = ["a", "b", "c"]
        equalString(lst) ---> "a=b=c"
    '''
    content = ""
    for i in lst:
        if lst.index(i) == len(lst)-1:
            content += "{}".format(i)
        else:
            content += "{} = ".format(i)
    return content