import sys, torndb, MySQLdb

def get_kpv_new_file():
    db = torndb.Connection('localhost','skytek',user='admin',password='5Am5on45!')
    #db.execute("update table kpv se `test` float(10) default 0;")
    kpv_new = []
    kpv_desc = []
    try: 
        file_o = open("kpv_new.txt","r+")
    except:
        print("Not able to open the kpv_new.txt file")
    else: 
        try:
            rd_all = file_o.readlines() # read in all lines of file
        except:
            file_o.close()
            print("kpv_new file did not read in")
        else: # all lines read in
            file_o.close()
            for i, val in enumerate(rd_all):
                vals = str.replace(val,'\n','')
                kpv_desc.append(vals)
                #print(vals)
                dtype = str(val[1])
                if dtype == 'i':
                    dt = 'int(10)'
                elif dtype == 'f':
                    dt = 'float(10)'
                elif dtype == 's':
                    dt = 'varchar(30)'
                #print(dt)
                #db.execute("alter table kpv add `" + vals + "` " + dt + " default 0;")

    try:
        file_o = open("kpv_new_vals.txt","r+")
    except:
        print("Not able to open the kpv_new_vals.txt file")
    else:
        try:
            rd_all = file_o.readlines() # read in all lines of file
        except:
            file_o.close()
            print("kpv_new_vals file did not read in")
        else: # all lines read in
            file_o.close()
            for i, val in enumerate(rd_all):
                vals = str.replace(val,'\n','')
                print('%s : %s'%(kpv_desc[i],vals))
                db.execute("update kpv set `" + i + "` = '" + vals + "';")


if __name__ == '__main__':
    get_kpv_new_file()
