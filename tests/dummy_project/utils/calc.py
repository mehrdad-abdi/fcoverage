from lib.util import greet, add_numbers


class Calculator:
    bias = 0

    def subtract(self, a, b):
        return self.bias + a - b

    def multiply(self, a, b):
        return self.bias + (a * b)

    def add(self, a, b):
        return self.bias + add_numbers(a, b)
