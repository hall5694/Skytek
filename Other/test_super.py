# pizza.py
class Main(object):
    def c_print(self, msg):
        print(msg)

class Sub(Main):
    def startit(self):
        super().c_print("message")

if __name__ == '__main__':
    Sub().startit()