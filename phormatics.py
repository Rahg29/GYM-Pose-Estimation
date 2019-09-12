import final

class Phormatic(object):
    
    output = ''
    FILE_PATH = ''
    EXERCISE_TYPE = ''
    size = (240, 240)
    
    def __init__(self, FILE_PATH,EXERCISE_TYPE):
        self.EXERCISE_TYPE = EXERCISE_TYPE
        self.FILE_PATH = FILE_PATH
    
    def run(self):
        output = final.run(self.FILE_PATH,self.EXERCISE_TYPE,self.size)

ph = Phormatic('/home/bindadeepanshu/Notebooks/phormatics/vlc-record-2019-09-04-12h15m32s-87954.com.mp4-.mp4','pullup')
output = ph.run()