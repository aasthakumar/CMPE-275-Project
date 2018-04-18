import uuid


def process(file_obj, request = True, name=""):
    if request:
        name = uuid.uuid4().hex
        file_obj.save(os.path.join("/tmp", name))
    with open(name) as f:
        process = False
        chunk_size = 500
        data = []
        for line in f:
            #print line.strip().split()
            if len(line.strip().split())>0 and (line.strip().split())[0] == "STN":
                process = True
                continue
            
            if process:
                data.append(line)
                
            if len(data) ==chunk_size:
                print ("Yielding data ",len(data))
                yield(data)
                data =[]
    if data:
        print ("Yielding data ",len(data))
        yield(data)
        
        
if __name__ == '__main__':
    f =  open("data/meso.out")
    for x in process(None, request=False, name = "data/meso.out"):
        print ("".join(x))