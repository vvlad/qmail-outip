
import socket
from log import warning,debug,info,critical,error,exception

__lookup_cache__ = {}

class IpAddress:
  def __init__(self, ip_address, default_helo_host= None, subnet = None):
    self.subnet = subnet 
    self.ip_address = ip_address
    if hasattr(socket, 'setdefaulttimeout'): socket.setdefaulttimeout(0.25)
    
    try:
      self.helo_host = __lookup_cache__[self.ip_address] = __lookup_cache__.get(self.ip_address) or socket.gethostbyaddr(self.ip_address)[0]
    except socket.herror as error:
      warning("I wasn't able to lookup the reverse for %s using %s"%(self.ip_address, default_helo_host))
      self.helo_host = default_helo_host
    
  def __str__(self):
    return "<IpAddress address=%s helo=%s>"%(self.ip_address, self.getHeloHost())

  def getIpAddress(self): return self.ip_address

  def getHeloHost(self): return self.helo_host

  def getSubnet(self): return self.subnet
  
  def makeBlacklisted(self): self.subnet.blacklistIpAddress(self.ip_address)


