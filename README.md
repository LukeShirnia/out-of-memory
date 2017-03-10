# Out-Of-Memory Investigation .py


The following python script can be used to calculate the estimated RSS (RAM) value of each service moments before the OOM incident. The system logs the RSS values of all processes at the time OOM is invoked, the file will calculate how much RAM your service was theorietically trying to use and how much it actualy has 


The script looks in /var/log/messages and takes the values recorded by the system just before the incident occurs. 






Current usage is as follows:

```
curl -s https://raw.githubusercontent.com/LukeShirnia/out-of-memory-investigation.py/master/oom.py | python
```

The script currently works on the following OS:

..* RedHat 5,6,7

..* CentOS 5,6,7

..* Ubuntu 14.04LTS

Testing for Debian and Ubuntu to commence shortly 



###Example Output

```
----------------------------------------

      _____ _____ _____
     |     |     |     |
     |  |  |  |  | | | |
     |_____|_____|_|_|_|

     Out Of Memory Analyser

----------------------------------------
**************************************************
         !!!!OOM ISSUE!!!!
This device HAS run out of memory recently
**************************************************

----------------------------------------
Dates OOM occured:    Mar, 9, 10:58:55
Sytem RAM:             987 MB
Estimated RAM at OOM: 1509 MB
Services Killed:      mysqld, apache
----------------------------------------
Top 5 RAM Consumers at time of OOM:
----------------------------------------
Service: apache2               1370 MB
Service: mysqld                251 MB
Service: 4                     59 MB
Service: driveclient           12 MB
Service: fail2ban-server       10 MB
----------------------------------------


----------------------------------------
Dates OOM occured:    Mar, 9, 10:59:57
Sytem RAM:             987 MB
Estimated RAM at OOM: 1555 MB
Services Killed:      mysqld
----------------------------------------
Top 5 RAM Consumers at time of OOM:
----------------------------------------
Service: apache2               1160 MB
Service: mysqld                230 MB
Service: driveclient           16 MB
Service: sshd                  16 MB
Service: rackspace-monit       15 MB
----------------------------------------


----------------------------------------
Dates OOM occured:    Mar, 9, 11:37:32
Sytem RAM:             987 MB
Estimated RAM at OOM: 1369 MB
Services Killed:      mysqld
----------------------------------------
----------------------------------------
Top 5 RAM Consumers at time of OOM:
----------------------------------------
Service: apache2               1041 MB
Service: mysqld                197 MB
Service: sshd                  24 MB
Service: driveclient           16 MB
Service: rackspace-monit       15 MB
----------------------------------------


----------------------------------------
Dates OOM occured:    Mar, 9, 11:49:23
Sytem RAM:             987 MB
Estimated RAM at OOM: 1792 MB
Services Killed:      mysqld
----------------------------------------
----------------------------------------
Top 5 RAM Consumers at time of OOM:
----------------------------------------
Service: apache2               1480 MB
Service: mysqld                207 MB
Service: sshd                  10 MB
Service: fail2ban-server       9 MB
Service: polkitd               8 MB
----------------------------------------
```
