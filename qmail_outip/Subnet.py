from time import time
import log as logger
from ipaddr import IPv4Address 
from IpAddress import IpAddress
import sys
from log import warning,debug,info,critical,error,exception

class Subnet(object):
  
  DEFAULT_MESSAGE_RATE = 10
  DEFAULT_INTERVAL = 1

  def __init__(self,config):
    self.config = config 
    _range = xrange(0,0)
    self.max_messages = Subnet.DEFAULT_MESSAGE_RATE
    self.max_interval = Subnet.DEFAULT_INTERVAL
    self.helo_host = config.get('fallback_helo_host')
    self.errors = {}

    if self.helo_host is None:
      error("Missing fallback_helo_host for subnet %s"%(config)) 
      sys.exit(1)

    self.current_address = None
    if config.has_key('range'):
      start,stop = config['range'].split("-",2)
      _range = range( int(IPv4Address(start))-1, int(IPv4Address(stop)) )


    if config.has_key("max_messages"): self.max_messages = config["max_messages"]
    if config.has_key("max_interval"): self.interval = config["max_interval"]

    self.range = _range
    self.reset()
    self.blacklist = []

  def __str__(self):

    return "<Subnet range=%s current_address=%s max_messages=%d current_messags=%d max_interval=%d current_interval=%d>"%(
        self.config["range"],
        self.current_address,
        self.max_messages,
        self.current_messages,
        self.interval,
        time()-self.last_request
    )

  def reset(self):
    self.exhausted = False
    self.current_messages = 0
    self.last_request = 0
    self.iterator = self.range[0] 

  def isExhausted(self):
    if self.exhausted:
      now = time()
      seconds = now - self.last_request
      
      if seconds > self.max_interval: self.reset()
    
    return self.exhausted


  def getIpAddress(self):
    now = time()
    seconds = now - self.last_request
    
    if seconds > self.max_interval:
      debug("Timeout reached for %s moving to the next address"%(self))
      self.nextIpAddress()
    
    if self.current_messages >= self.max_messages:
      debug("Message limit reached for %s moving to the next address"%(self))
      self.nextIpAddress()
    
    if self.current_address:
      self.current_messages += 1

    self.last_request = now
    return self.current_address

  def nextIpAddress(self):
    self.current_address = None
    scans = 0

    while self.iterator < self.range[-1]:
      self.iterator += 1
      address = IpAddress(str(IPv4Address(self.iterator)), default_helo_host = self.helo_host, subnet = self)
      
      if address.ip_address in self.blacklist:
        error("%s is blacklisted",address.ip_address)
        continue
      
      self.current_address = address 
      self.current_messages = 0
      self.last_request = 0
      info(self)
      return self.current_address
   
    #cur = self.range[0]
    #debug("End of subnet reached resetting")
    #while cur < self.iterator:
    #  address = IpAddress(str(IPv4Address(cur)), default_helo_host = self.helo_host, subnet = self)

    #  if address.ip_address in self.blacklist:
    #    error("%s is blacklisted",address.ip_address)
    #    continue
      
    #  self.current_address = address 
    #  self.current_messages = 0
    #  self.last_request = 0
    #  self.interator = cur
    #  info(self)
    #  return self.current_address
    
    self.exhausted = True
    return None

  def getMaxErrorsCount(self): return self.config.get('max_errors') or 50

  def blacklistIpAddress(self, ip_address):
    
    value = 1
    errors = self.errors

    if errors.has_key(ip_address):
      value = errors.get(ip_address) + 1
      if value >= self.getMaxErrorsCount():
        error("%d errors for %s blacklisted",value, ip_address)
        self.blacklist.append(ip_address)
    else:
      value = 1
    
    warning("%d errors for %s",value, ip_address)

    errors[ip_address] = value







