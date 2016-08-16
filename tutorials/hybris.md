----------


Hybris
=====

### Download
SAP do not provide package to the public, you can download it from your SAP account.
### Installation for production
#### Create hybris user
```bash
mkdir /home/app/hybris
useradd hybris -d /home/app/hybris
```
#### Unzip package
```bash
mkdir ~/src
unzip HYBRISCOMM55100P_8-70000793.zip -d ~/src
mv ~/src/hybris/bin /home/app/hybris/
chown -R hybris: /home/app/hybris/
chmod -R 755  /home/app/hybris/
```

#### Build
```bash
cd /home/app/hybris/bin/platform
. setantenv.sh 
ant clean all
Java HotSpot(TM) 64-Bit Server VM warning: ignoring option MaxPermSize=256M; support was removed in 8.0
Buildfile: /home/app/hybris/bin/platform/build.xml
     [echo] /home/app/hybris/bin/platform/tomcat/bin
     [echo] /home/app/hybris/bin/platform/ext/core/web/webroot/WEB-INF/external-dependencies.xml was not found!
    [mkdir] Created dir: /home/app/hybris/log
    [mkdir] Created dir: /home/app/hybris/data
    [mkdir] Created dir: /home/app/hybris/temp/hybris
    [mkdir] Created dir: /home/app/hybris/roles
    [input] 
    [input]  **** NO CONFIG FOLDER FOUND ****
    [input] 
    [input]  No config folder was found at /home/app/hybris/config.
    [input]  A "fresh" folder containing basic configuration files and the hybris 
    [input]  demo licence will be created for your convenience.
    [input]  Please adjust and review the configuration files (and license) and 
    [input]  call 'ant' again. This directory will never be overridden or 
    [input]  touched again. Always use this configuration folder for configuration 
    [input]  of platform, do not change anything within the platform folder.
    [input] 
    [input]  Please choose the configuration template. 
    [input]  Press [Enter] to use the default value ([develop], production)
production
    [input] 
    [input]  Used Java memory. This depends on the memory available on the host 
    [input]  and the operating system used.  
    [input]  You can always modify the setting later in your config/local.properties.
    [input]  Press [Enter] to use the default value [3G]
6G

```
#### Write Sysv init.d script
Add to /etc/init.d/hybris
```bash
#!/bin/bash
# Hybris init script

# chkconfig: 345 80 30
# description: Hybris

# Prepare
export RUN_AS_USER="hybris"
hybris_wrapper="/home/app/hybris/bin/platform/tomcat/bin/wrapper.sh"         

# Send all task to Hybris wrapper
"${hybris_wrapper}" "$@"

# Clean up
unset RUN_AS_USER

```

Make the script executable
```bash
chmod +x /etc/init.d/hybris
```



