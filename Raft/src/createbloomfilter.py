from bloomfilter import BloomFilter
import datetime

def to_integer(dt_time):
        #dt_time = datetime.datetime.strptime(dt, "%Y-%m-%d")
        return 10000*dt_time.year + 100*dt_time.month + dt_time.day

class CreateBloomFilter():
    def __init__(self,cnt, word_present):
        self.n = 1000000
        self.word_present = word_present #no of items to add
        self.p = 0.05 #false positive probability
        self.bloomf = BloomFilter(self.n,self.p)
        for item in self.word_present:
            print(item)
            self.bloomf.add(bytes(to_integer(datetime.datetime.strptime(item,'%Y%m%d'))))
    
    def createfilter(self, cnt, word_present):
        self.p = 0.05 #false positive probability
        self.bloomf = BloomFilter(cnt,self.p)
        for item in word_present:
            self.bloomf.add(bytes(to_integer(item)))
    
    def testdate(self, todate):
        todate = datetime.datetime.strptime(todate,'%Y%m%d')
        todate = to_integer(todate)
        if self.bloomf.check(bytes(todate)):
            return 1
        else:
            return 0
        
