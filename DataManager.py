import os
import json
import random, string
import dateutil.parser
import threading


class DataManager(object):
    __instance = None
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(DataManager,cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):      
        if(self.__initialized): return
        self.__initialized = True
        #print ("INIT DATA MANAGER")
        dataFile = 'dati.json'
        try:
            self.jsonfile = open(dataFile, 'r+')
            self.data = json.load(self.jsonfile)
        except Exception: #file non esiste
            with open(dataFile, 'a+') as f:
                self.data = {"users": [], "logs": [] }
                f.seek(0)
                f.write(json.dumps(self.data, indent=4))
                f.truncate()
                os.chmod(dataFile, 0o666)
            self.jsonfile = open(dataFile, 'r+')
        
    
    def get_all_data(self):
        return self.data
    
    def get_node(self,node,queryRequest={}):
        if not node in self.data:
            return {"error" : "Not Found"}
        
        result = self.data[node]
        if queryRequest == {} or queryRequest == None:
            return {node : result}
        print("trovata una query")
        n_req = len(queryRequest)
        query_res = []
        for row in result:
            n = 0
            for key,value in queryRequest.items():
                if key in list(row.keys()):
                    if row[key] == value:
                            n += 1
            if n == n_req:
                query_res.append(row)
        return {node : query_res}
    
    def import_logs(self,mode,edit=True):
        logs = DataManager().get_node("logs")
        #print(json.dumps(logs["logs"], indent=4))
        users = DataManager().get_node("users")
        if "error" in logs.keys() or "error" in users.keys():
            return {"error" : "Not Found"}
        if mode == "all":
            pass
        elif mode == "new":
            logs["logs"] = [x for x in logs["logs"] if x["downloaded"] == "0"]
        else:
            return {"error" : "Not Found"}
        logsToExport = {"logs" : []}
        logsToEdit = []
        for log in logs["logs"]:
            user = DataManager().get_object_for_id("users",log["user_ref"])
            if len(user) > 1:
                return {"error" : "Not Found"}
            if len(user) == 1:
                name = user[0]["name"]
                uid = user[0]["id_card"]
            #DateTime = dateutil.parser.parse(log["dateTime"]).strftime('%d/%m/%Y %H:%M:%S')
            #Status = log["status"]
                logsToExport["logs"].append({"Name": name, "UID": str(uid), "DateTime": log["dateTime"], "Status":log["status"], "logId" : log["id"], "downloaded" : log["downloaded"]})
            #self.edit_row("logs",log["id"],{"downloaded" : "1"})
                if log["downloaded"] == "0":
                    logsToEdit.append(log["id"])
        #print(json.dumps(logsToExport, indent=4, sort_keys=True))
        if edit == True:
            thread = threading.Thread(target = self.editImported, args=[logsToEdit])
            thread.daemon = True
            thread.start()
        return logsToExport
    
    def editImported(self, logsIds):
        for id in logsIds:
            self.edit_row("logs",id,{"downloaded" : "1"})
            
        
    
    def get_object_for_id(self,node,row_id):
        if not node in self.data:
            return {"error" : "Not Found"}
        
        result = self.data[node]
        r = [r for r in result if r['id'] == row_id]
        return r

    def add_row(self,node,request):
        if not node in self.data:
            return {"error" : "Not Found"}
        
        if not request:
            return {"error":"the request is empty"}
        new_row = {
        'id' : self.random_string(6)
            }
        for key,value in request.items():
            if key != "id":
                new_row[key] = value
        if not node in self.data:
            self.data[node] = [new_row]
        else:
            self.data[node].append(new_row)
        
        self.jsonfile.seek(0)
        self.jsonfile.write(json.dumps(self.data, indent=4))
        self.jsonfile.truncate()
        return new_row
    
    def delete(self,node,row_id):
        if not node in self.data:
            return {"error" : "Not Found"}
        
        result = self.data[node]
        row = [row for row in result if row['id'] == row_id]
        if len(row) == 1:
            result.remove(row[0])
            self.jsonfile.seek(0)
            self.jsonfile.write(json.dumps(self.data, indent=4))
            self.jsonfile.truncate()
            return {"result" : True}
        else:
            return {"result" : False}
    def edit_row(self,node,row_id,request):
        print(str(request))
        if not node in self.data:
            return {"error" : "Not Found"}
        if not request:
            return {"error":"the request is empty"}
        if type(request) is not dict or request == None:
            return {"error":"the request is not a valid Dictionary"}
        res = self.data[node]
        r = [r for r in res if r['id'] == row_id]
        if len(r) != 1:
            return {"error":"id not found"}
        for key,value in request.items():
            if key != "id":
                r[0][key] = value
        self.jsonfile.seek(0)
        self.jsonfile.write(json.dumps(self.data, indent=4))
        self.jsonfile.truncate()
        return r[0]
  
                    
        
        
    
    def random_string(self,length):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))

#if __name__ == "__main__":
    #DataManager().import_logs("all")
        

    
        

