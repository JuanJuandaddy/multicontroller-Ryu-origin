# -*-coding:utf-8-*-
# -*-this is a python script -*-
import time

import re

src_file="./echarts_test"

dst_file="./div_option.py"
class run(object):
    @staticmethod
    def str_repl(s):

        res=s.group().split(":")[0]

        return f'\"{res}\":'

    @staticmethod
    def bool_repl(b):

        res=list(b.group())

        res[0]=res[0].upper()

        return f'{"".join(res)}'

    @classmethod
    def sub(cls):
        res=""
        with open(src_file,"r+") as f:
            content=f.read()

            str_reg=re.compile(r"\w+:")

            res+=re.sub(str_reg,cls.str_repl,content)

            #检查value是否有布尔型
            bool_reg=re.compile(r'false|true')

            res=re.sub(bool_reg,cls.bool_repl,res)


        print(f'{src_file} ==>读取Echarts文件完成')


        time.sleep(0.1)

        with open(dst_file,"w+") as f:

            f.writelines(res)

        print(f'更新Echarts文件完成==> {dst_file} ')

def update(value,*args):

  command='option'

  for i in args:

    if i.isdigit():

      command += f'[{i}]'

    else:

      command += f'["{i}"]'

  eval(f'{command}={value}')

def get_option():

    #return option
    pass

if __name__ == '__main__':
    run.sub()
    print("替换完成")