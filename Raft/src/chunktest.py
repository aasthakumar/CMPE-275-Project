import uuid
import datetime

def process(file_obj, request = True, name=""):
    if request:
        name = uuid.uuid4().hex
        file_obj.save(os.path.join("/tmp", name))
    with open(name) as f:
        if name.endswith('.out'):
        
            process = False
            chunk_size = 500
            data = []
            for line in f:
                #print line.strip().split()
                if len(line.strip().split())>10 and (line.strip().split())[0] == "STN":
                    process = True
                    continue
                
                if process:
                    tempLine = line.strip().split()
                    tempLine[1] = datetime.datetime.strptime(tempLine[1], '%Y%m%d/%H%M').strftime('%Y-%m-%d %H:%M:%S')
                    data.append(','.join(tempLine)+"\n")
                    
                if len(data) ==chunk_size:
                    print ("Yielding data ",len(data))
                    yield(data)
                    data =[]
            if data:
                print ("Yielding data ",len(data))
                yield(data)
        else:
            process = False
            chunk_size = 500
            data = []
            #20050621_0800
            print("mesnet file",name[-17:])
            data_timestamp = datetime.datetime.strptime(name[-17:].split(".")[0], '%Y%m%d_%H%M').strftime('%Y-%m-%d %H:%M:%S') 
            line_c = 0
            for line in f:
                #print (line.strip().split())
                line_c+=1
                if line_c==1:
                    process = True
                    continue
                if process:
                    tempLine = line.strip().split(',')
                    if len(tempLine)!=11:
                        continue
                    newTempLine =["NULL"]*11
                    newTempLine[0] = tempLine[0]
                    newTempLine[1] = data_timestamp
                    newTempLine[3] = tempLine[3]
                    newTempLine[4] = tempLine[4]
                    newTempLine[5] = tempLine[5]
                    #tempLine[1] = datetime.datetime.strptime(tempLine[1], '%Y%m%d/%H%M').strftime('%Y-%m-%d %H:%M:%S')
                    print("appendinhg")
                    data.append(','.join(newTempLine)+"\n")
                    
                if len(data) ==chunk_size:
                    print ("Yielding data ",len(data))
                    yield(data)
                    data =[]
            if data:
                print ("Yielding data ",len(data))
                yield(data)
            
            
            
        
