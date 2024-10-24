import yaml
import pandas as pd
from CustomClass.CustomClass import *

class SymbolTable:
    def __init__(self):
        self.symbols = {}

    def add_symbol(self, name, value, sym_type="attribute", dif=0):
        # 添加符号到符号表
        symbol = {
            'name': name,
            'value': value,
            'type': sym_type,
            'dif': dif
        }
        # 通过name作为key插入或更新字典
        self.symbols[name] = symbol

    def get_symbol(self, name):
        # 查询符号表中的符号
        return self.symbols.get(name, None)

    def __repr__(self):
        return f"SymbolTable({self.symbols})"
    
def load_attributes_into_symboltable(attributes):
    for attribute in attributes:
        name = attribute['name']
        attr_type = attribute['type']
        params = attribute['params']

        # 将参数格式化为字符串
        params_str = ', '.join(map(str, params))
        value = f"{attr_type}({params_str})"

        # 将symbol添加到符号表
        symbol_table.add_symbol(name, value)

# 将表格加载到符号表中，表格中的属性通过符号表查询
def load_tables_into_symboltable(tables):
    for table in tables:
        table_name = table['name']
        attributes = table['attributes']

        # 从符号表中查询表的每个属性的值，并组合成表格的value
        table_value = ', '.join([symbol_table.get_symbol(attr)['value'] for attr in attributes])

        # 将表格作为符号添加到符号表
        symbol_table.add_symbol(table_name, table_value)

# Initialize SymbolTable
symbol_table = SymbolTable()