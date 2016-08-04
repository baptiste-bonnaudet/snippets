Forward history to rsyslog and to a remote server
=======

If for multiple reasons you need to log activity on a server to a syslog you have 3 choices :

 1. Modifying the PROMPT_COMMAND 	 
 - Pros: easy, efficient
 - Cons: a user can unset the environment variable
 2. Adding a bash trap 
  - Pros: easy, efficient
 - Cons: a user can unset the trap, it will spawn a process at each command a user enters
 3. Patching bash
 - Pros: transparent, secure
 - Cons: you need to patch bash
 
We will see here how to do the 1st one and forward everything to a remote server.
 
```bash
# configure rsyslog to forward to a remote server
cat << EOF >> /etc/rsyslog.conf
*.*                                          @mykiwi.example.com:514
EOF

# add syslog configuration
cat << EOF > /etc/rsyslog.d/hack.conf
*.*;auth,authpriv.none,local6           -/var/log/syslog
local6.info                     /var/log/history.log
EOF

# create history log file
touch /var/log/history.log

# add promt command to log bash history (replace /etc/bash.bashrc with /etc/bashrc on CentOS/RHEL)
cat << EOF >> /etc/bash.bashrc
PROMPT_COMMAND='history -a >(tee -a ~/.bash_history | logger -p local6.info -t "$USER[$$] $SSH_CONNECTION")'
EOF
```

