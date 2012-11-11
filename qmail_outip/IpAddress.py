
import socket
import logging

logger = logging.getLogger("outip")

class IpAddress:
  def __init__(self, ip_address, default_helo_host= None):
   
    self.ip_address = ip_address
    if hasattr(socket, 'setdefaulttimeout'): socket.setdefaulttimeout(0.25)
    
    try:
      self.helo_host = socket.gethostbyaddr(self.ip_address)[0]
    except socket.herror as error:
      logger.warning("I wasn't able to lookup the reverse for %s using %s"%(self.ip_address, default_helo_host))
      self.helo_host = default_helo_host
    
  def __str__(self):
    return "<IpAddress address=%s helo=%s>"%(self.ip_address, self.getHeloHost())

  def getIpAddress(self): return self.ip_address

  def getHeloHost(self): return self.helo_host
