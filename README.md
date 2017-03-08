# Out-Of-Memory Investigation .py


The following python script can be used to calculate the estimated RSS value of service after and OOM incident. 


The script looks in /var/log/messages and takes the values recorded by the system just before the incident occurs. 


Current usage is as follows:

```
curl -s https://raw.githubusercontent.com/luke7858/out-of-memory-investigation.py/master/oom.py | python - /var/log/messages
```

Please replace `/var/log/messages` with you OOM log file (eg. `/var/log/syslog.1`)

This will be changed shortly to investigate the appropriate log file depending on the OS
