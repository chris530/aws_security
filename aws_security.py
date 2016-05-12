#!/usr/bin/env python
#
#  Created by Chris Haesig 2016
#

yaml_file = 'settings.yml'

import yaml, re, sys, StringIO, getpass
from boto.ec2.connection import *

# Error function

def error_func(txt):
  print txt
  raise SystemExit

# connect to AWS api via boto

def aws_connect():
  
   #connect to aws 

   awsfh = EC2Connection(yaml_settings['awsaccesskey'], yaml_settings['awssecretkey'], is_secure = True) 
   instance = awsfh.get_all_instances(filters={'instance_id':instance_name})
   if len(instance) > 0:

     # get vpc id 

     vpc_id = instance[0].instances[0].vpc_id
   
     print
     print sys.argv[1], 'is using VPC:', vpc_id   
     print

     print "Dumping firewall rules"
     print "-"*100
     print 

     # loop throup found groups

     for group_name in instance[0].instances[0].groups:
       print
       print "Group: ",group_name.name
       print

       # take the group name, find the firewall settings

       sgfilter = {'group-name': group_name.name, 'vpc-id': vpc_id } 
       for sg in  awsfh.get_all_security_groups(filters=sgfilter):
         for fw in sg.rules:
           print fw.ip_protocol,' from', fw.grants[0]," ports: ",fw.from_port, fw.to_port

   else:
     error_func("Could not find instance")
   
# Sever Connect

def server_connect():

  from fabric.api import run, env, sudo, settings
  from fabric.tasks import execute
  env.password = getpass.getpass("Please enter sudo password: ") 

  def runcmds():

    print "Running iptables"
    buf = StringIO.StringIO();
    ipinfo = sudo('iptables --list',stdout=buf)
    print buf.getvalue()

    print "Running last"
    buf = StringIO.StringIO();
    ipinfo = sudo('last',stdout=buf)
    print buf.getvalue()

    print "Running w"
    buf = StringIO.StringIO();
    ipinfo = sudo('w',stdout=buf)
    print buf.getvalue()

    print "Running auth.log"
    buf = StringIO.StringIO();
    ipinfo = sudo('tail /var/log/auth.log',stdout=buf)
    print buf.getvalue()

    # Looks for Users that have a uid of 0 or guid of 0

    print "Looking for users that have a UID of 0"
    buf = StringIO.StringIO();
    ipinfo = sudo('cat /etc/passwd',stdout=buf)
    etcfile = buf.getvalue()

    etcar = etcfile.split('\n')
    for userst in etcar:
      if 'home' in userst or 'root' in userst:
        if userst.split(':')[3] == '0' or userst.split(':')[4] == '0':
          print "FOUND"
          print userst.split(':')[1], userst.split(':')[3], userst.split(':')[4] 

  env.use_ssh_config = True
  execute(runcmds,hosts=["{}@{}".format(yaml_settings['sshuser'],yaml_settings['jumphost'])])


# Read Yaml file

def read_yaml():
  try:
    fh = open(yaml_file).read()
    y = yaml.safe_load(fh)['awssecurity']
    return y
  except:
    error_func("Could not open {} file".format(yaml_file))

# Entry 

if __name__ == '__main__':

  if len(sys.argv) != 2:
    print '''
usage aws_security.py <instance_id>
    '''
    error_func("Please run command with instance name")
  else:
    # regex makes sures the i-233233  format 
    instance_name = sys.argv[1] if re.search('^i\-[a-zA-Z0-9]*$',sys.argv[1]) else error_func("Instance name is invalid")

  yaml_settings = read_yaml()

  # enables awsinfo 
 
  if yaml_settings.has_key('awsinfo'): 
    aws_connect()
    
  if yaml_settings.has_key('serverconnect'):
    if yaml_settings.has_key('sshuser') and yaml_settings.has_key('jumphost'): 
      server_connect()

