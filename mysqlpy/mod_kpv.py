import sys, torndb, MySQLdb

def get_kpv_new_file():
    db = torndb.Connection('localhost','skytek',user='admin',password='5Am5on45!')
    kpv_vals_list = []
    user = 'default_user'

    i = 0
    #db.execute("update kpv set `" + str(i) + "` = '" + str(kpv_vals_list[i]) + "' where user = '" + str(user) + ";")
    try:
        kpv_vals_file = open("kpv_vals.txt","r+")
    except:
        print("Not able to open the kpv_vals.txt file")
        raise
    else:
        try:
            kpv_vals = kpv_vals_file.readlines() 
        except:
            kpv_vals_file.close()
            print("kpv_new_vals file did not read in")
        else: # all lines read in
            kpv_vals_file.close()
            for i, val in enumerate(kpv_vals):
                vals = str.replace(val,'\n','')
                kpv_vals_list.append(vals)
    # generate vals list --------------------------------


         
    # generate index columns and fill default values-----
    try: 
        kpv_tags_file = open("kpv_tags.txt","r+")
    except:
        print("Not able to open the kpv_tags.txt file")
    else: 
        try:
            kpv_tags = kpv_tags_file.readlines() 
        except:
            kpv_tags_file.close()
        else: 
            kpv_tags_file.close()
            for i, val in enumerate(kpv_tags):
                tag = str.replace(val,'\n','')
                dtype = str(tag[1])
                if dtype == 'i':
                    dt = 'int(10)'
                elif dtype == 'f':
                    dt = 'float(10)'
                elif dtype == 's':
                    dt = 'varchar(30)'
                db.execute("alter table kpv add `row" + str(i) + "` text(30) default '" + str(kpv_vals_list[i]) +  "';")
                db.execute("update kpv set `row" + str(i) + "` = '" + str(tag) + "' where user = 'tags';")
    # generate index columns-----------------------------


if __name__ == '__main__':
    get_kpv_new_file()
