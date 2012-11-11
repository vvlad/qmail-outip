
from Subnet import Subnet
import logging

logger = logging.getLogger("outip")

class IpPool(object):

  def __init__(self,name, config):
    self.subnets = [Subnet(spec) for spec in config['subnets']]
    self.current_subnet = None
    self.name = name
    self.config = config
    logger.info(self)

  def getConfig(self): return self.config
  def getName(self): return self.name
  
  def isCacheable(self): return self.config.get("disable_cache") != True

  def __str__(self):
    return "<IpPool name=%s subnets=%d doing_cache=%s subnet=%s>"%(
        self.name,
        len(self.subnets),
        self.current_subnet,
        self.isCacheable())

  def nextAddress(self):
    seen = list()
    ip_address = None
   
    while len(seen) != len(self.subnets):
      subnet = self.getSubnet()
      if subnet:
        logger.debug("Looking at %s",subnet)
        seen.append(subnet)
        ip_address = subnet.getIpAddress()
        if ip_address is None:
          logger.warning("No address found for %s trying next subnet if any"%(subnet))
          continue
        else:
          logger.debug("Ok got %s from %s"%(ip_address,subnet))
          break

      else:
        logger.debug("No available subnets found")
        return None
    return ip_address

  def getSubnet(self):
    if self.current_subnet and not self.current_subnet.isExhausted():
      logger.debug("Ok %s might have additional capacity"%(self.current_subnet))
      return self.current_subnet
    
    self.current_subnet = None

    for subnet in self.subnets:
      if not subnet.isExhausted():
        logger.debug("Trying subnet %s"%(subnet))
        self.current_subnet = subnet
        break
      else:
        logger.warning("Found %s subnet but it's exhaused"%(subnet))
    
    return self.current_subnet

