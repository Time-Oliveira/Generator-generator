class DerivedTable:
    def __init__(self):
        self.values = {}

    def add_value(self, name, value):
        # 添加值到派生表
        derived_value = {
            'name': name,
            'value': value,
        }
        # 用name作为key插入或更新字典
        self.values[name] = derived_value

    def get_value(self, name):
        # 从派生表中查询值
        # return self.values.get(name, None)
        if self.has_value(name):
            return self.values.get(name)['value']

    def has_value(self, name):
        return name in self.values
    
    def __repr__(self):
        return f"DerivedTable({self.values})"
    
def load_constants_into_derivedtable(constants):
    for constant in constants:
        for name, value in constant.items():
            derived_table.add_value(name, value)

derived_table = DerivedTable()