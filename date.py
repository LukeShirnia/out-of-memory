import datetime

date_string = ['11:11:12', '10:10:15', '21:12:00', '19:19:19']
date_object = []

for i in date_string:
	temp_date_string = datetime.datetime.strptime(i, "%H:%M:%S")
#	print temp_date_string
	date_object.append(temp_date_string)
	date_object.sort()

for y in date_object:
	print y.strftime('%H:%M:%S')
