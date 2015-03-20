'''
Created on 16-Mar-2015

@author: aithal
'''
from stem import CircStatus, UNDEFINED
from stem.control import Controller
from stem.descriptor import Descriptor
from stem import descriptor
from stem.descriptor.remote import DescriptorDownloader
from stem import CircStatus
from stem.descriptor import parse_file, DocumentHandler
from stem.descriptor.networkstatus import NetworkStatusDocumentV3,\
    NetworkStatusDocumentV2

import os
import StringIO
import socket
import urllib
import time
import socks  # SocksiPy module
import stem.process
from stem import Signal
from stem.util import term
from stem.control import Controller
from stem.descriptor import parse_file

SOCKS_PORT = 7000
socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', SOCKS_PORT)
__originalSocket = socket.socket


def getaddrinfo(*args):
  return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (args[0], args[1]))]

socket.getaddrinfo = getaddrinfo


def query(url):
  try:
    return urllib.urlopen(url).read()
  except:
    return "Unable to reach %s" % url
  finally:
      socket.socket=__originalSocket
      
def print_bootstrap_lines(line):
  if "Bootstrapped " in line:
    print term.format(line)

def get_key(item):
    return item[3]
exit_digests = set()
entry_digests=set()
entry_fing=[]
exit_fing=[]

def get_entry_exit_fing():  
    with Controller.from_port(port=9151) as controller:
        controller.authenticate()
        data_dir = controller.get_conf('DataDirectory')
        
        for desc in controller.get_microdescriptors():
            if desc.exit_policy.is_exiting_allowed():
                exit_digests.add(desc.digest)
            else:
                entry_digests.add(desc.digest)
        global entry_fing,exit_fing
        for desc in parse_file(os.path.join(data_dir, 'cached-microdesc-consensus')): 
            if desc.digest in exit_digests :
                exit_fing.append((desc.fingerprint,desc.address,desc.nickname,desc.bandwidth))
            else:
                entry_fing.append((desc.fingerprint,desc.address,desc.nickname,desc.bandwidth))
    
        exit_fing=sorted(exit_fing,key=get_key,reverse=True)
        entry_fing=sorted(entry_fing,key=get_key,reverse=True)
    
get_entry_exit_fing()     


tor_process = stem.process.launch_tor_with_config(
config = {
    'SocksPort': str(SOCKS_PORT),
},
  init_msg_handler = print_bootstrap_lines,
)
socket.socket = socks.socksocket
print term.format("\nChecking our endpoint:\n")
start_time=time.time()
print term.format(query("https://www.atagar.com/echo.php"))
print "time taken %s secs"%(time.time()-start_time)
tor_process.kill()
socket.socket=__originalSocket

tor_process = stem.process.launch_tor_with_config(
config = {
    'SocksPort': str(SOCKS_PORT),
},
  init_msg_handler = print_bootstrap_lines,
)

with Controller.from_port(port=9151) as controller:
    controller.authenticate()
    controller.signal(Signal.NEWNYM)
    controller.extend_circuit('0', [entry_fing[0][0],entry_fing[1][0],exit_fing[0][0]])
    print(controller.get_info('circuit-status'))
    
socket.socket = socks.socksocket
print term.format("\nChecking our endpoint:\n")
start_time=time.time()
print term.format(query("https://www.atagar.com/echo.php"))
print "time taken %s secs"%(time.time()-start_time)
socket.socket=__originalSocket
tor_process.kill()
  