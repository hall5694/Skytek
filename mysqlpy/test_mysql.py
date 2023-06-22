import torndb, MySQLdb
from time import strftime,localtime

db = torndb.Connection('localhost','skytek',user='admin',password='5Am5on45!')

dtype = 'SP'
m_read = '50.03'
r_read = '50.01'
dtime = strftime("%Y%m%d%H%M%S", localtime())
#db.execute("INSERT INTO test_records(type,datetime,meter_read,reference_read) VALUES(" + str(dtype) + "," \
            #+ str(dtime) + "," + str(meter_read) + "," + str(reference_read) + ");")
db.execute("INSERT INTO test_records(type,datetime,meter_read,reference_read) VALUES('" + \
            dtype + "' , " + dtime + "," + m_read + "," + r_read + ");")
