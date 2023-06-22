import sys, torndb, MySQLdb

def get_kpv_new_file():
    kpv_types = []
    kpv_tags = []
    kpv_vals = []
    db = torndb.Connection('localhost','skytek',user='admin',password='5Am5on45!')
    dbq_kpv_tags = db.get("SELECT * FROM kpv where user = 'tags'")
    dbq_kpv_vals = db.get("SELECT * FROM kpv where user = 'default_user'")

    for i in range(len(dbq_kpv_tags) - 1):
        kpv_tags.append(dbq_kpv_tags['row' + str(i)])
        kpv_types.append(str(str(kpv_tags[i])[1]))
        kpv_vals.append(dbq_kpv_vals['row' + str(i)])
        print("[%s]  %s  = %s {%s}"%(i,kpv_tags[i],kpv_vals[i],kpv_types[i]))

if __name__ == '__main__':
    get_kpv_new_file()
