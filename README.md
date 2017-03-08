# Out-Of-Memory Investigation .py


The following python script can be used to calculate the estimated RSS value of service after and OOM incident. 


The script looks in /var/log/messages and takes the values recorded by the system just before the incident occurs. 






Current usage is as follows:

```
curl -s https://raw.githubusercontent.com/luke7858/out-of-memory-investigation.py/master/oom.py | python
```

The script currently works on the following OS:
..* RedHat 5,7,8
..* CentOS 5,6,7
Testing for Debian and Ubuntu to commence shortly 
