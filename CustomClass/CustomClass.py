# 定义字段对象，包含字段名和自定义的数据类型
import random
import string

# 自定义数据类型定义
class CustomInt:
    def __init__(self, min_value, max_value):
        self.data_type = int
        self.min_value = min_value
        self.max_value = max_value

    def generate(self):
        return random.randint(self.min_value, self.max_value)

class CustomString:
    def __init__(self, max_length):
        self.data_type = str
        self.max_length = max_length

    def generate(self):
        length = random.randint(1, self.max_length)
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

class CustomFloat:
    def __init__(self, precision, min_value, max_value):
        self.data_type = float
        self.precision = precision
        self.min_value = min_value
        self.max_value = max_value

    def generate(self):
        return round(random.uniform(self.min_value, self.max_value), self.precision)

class RandomSelector:
    def __init__(self, *values):
        self.data_type = list  # 或者其他合适的类型
        self.values = values  # 直接保存传入的多个参数

    def generate(self):
        return random.choice(self.values)
