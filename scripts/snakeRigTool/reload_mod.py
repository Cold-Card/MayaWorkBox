# -*- coding: utf-8 -*-
import os
import imp
import traceback

def getAllFiles(filePath, path=True):
    u'''
    获取filepath文件路径下所有文件名称，不论有多少个子文件夹，都能深度获取
    path参数默认为True，返回的列表会带上路径；如果为False则只返回所有模块名称列表
    '''
    if os.path.exists(filePath):
        moudleList = []
        for paths, dirnames, filenames in os.walk(filePath):
            for file in filenames:
                if path == False:
                    moudleList.append(os.path.basename(os.path.join(paths, file).replace('\\', '/')))
                else:
                    moudleList.append(os.path.join(paths, file).replace('\\', '/'))
        return moudleList

class Reload_Mod:
    u'''
    刷新模块,传入参数是一个文件夹路径，即 包的路径
    '''
    def __init__(self, folder_path):
        self.folder_path = folder_path.replace("\\", "/")
        self.base_package = os.path.basename(self.folder_path)
        self.path = self.folder_path.replace(self.base_package, '')

    @property
    def getAllPyFiles(self):
        u'''
        获取文件夹下所有py文件(带路径)，除了 __init__.py
        '''
        files = getAllFiles(self.folder_path)
        pyfiles = [file for file in files if os.path.splitext(file)[-1] == '.py' and '__init__' not in file and "install.py" not in file]
        return pyfiles

    @property
    def normPyPath(self):
        u'''
        将带路径的python文件字符规格化
        '''
        files = self.getAllPyFiles
        mod = [os.path.basename(file) for file in files]
        mods = [i.replace('.py', '') for i in mod]
        package = [os.path.dirname(file) for file in files]
        realpackage = [file.replace(self.path, '') for file in package]
        packages = [i.replace('/', '.') for i in realpackage]
        return [packages, mods]

    @property
    def moudule_string(self):
        u'''
        模块字符串
        '''
        importModuleList = []
        reloadModuleList = []
        for package, mod in zip(self.normPyPath[0], self.normPyPath[1]):
            import_string = "from {} import {}".format(package, mod)
            importModuleList.append(import_string)
            reload_string = "imp.reload("+"{})".format(mod)
            reloadModuleList.append(reload_string )
        return [importModuleList, reloadModuleList]

    @property
    def reload_module(self):
        u'''
        刷新模块
        '''
        n = 0
        al = 0
        for mod, remod in zip(self.moudule_string[0], self.moudule_string[1]):
            try:
                strToCmd([mod, remod])
                print(mod)
            except:
                print("# {} mod reload error".format(mod))
                traceback.print_exc()
                n += 1
            al += 1
        print("")
        if n == 0:
            print("# all modules/{} modules  reload complate !!!".format(al))
        else:
            print("# {} modules {} module reload error".format(al, n))

def strToCmd(strList):
    u'''
    字符串转换为可执行命令，相当于mel的eval语句
    '''
    for str_i in strList:
        exec(str_i)

def reloadPackage(package_path):
    u'''
    刷新插件包所有模块
    '''
    return Reload_Mod(package_path).reload_module