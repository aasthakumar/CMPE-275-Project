from dateutil import parser
import time

def getEpochTime(str_time):
    dt = parser.parse(str_time)
    try:
        epoch_time =  int(time.mktime(dt.timetuple())) * 1000 + dt.microsecond / 1000
        return epoch_time
    except:
        #some error here, return None
        return None
    


