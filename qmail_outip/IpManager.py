
from twisted.internet import protocol
from twisted.protocols.basic import LineReceiver
from time import sleep
import uuid
from log import warning,debug,info,critical,error,exception
import logging

logger = logging.getLogger("outip")

STATE_NEW = "new"
STATE_IP_SENT = "ip_send"
STATE_COMPLETED = "completed"


class IpManager(LineReceiver):

  delimiter = "\n"
  
  def __init__(self,allocator):
    self.allocator = allocator
    self.state = STATE_NEW
    self.ip_address = None
    self.uuid = uuid.uuid4().hex

  def connectionMade(self):
    debug("new connection")
  
  def connectionLost(self,reason):
    debug(reason.getErrorMessage())
    reason.cleanFailure()

  def lineReceived(self, line):
    logger.uuid = self.uuid
    line = line.strip()
    
    try:
      debug("Command received [%s]. State is '%s'"%(line,self.state)) 
      if self.state == STATE_NEW:
        debug("Processing ip request")
        self.processIpRequest(line)
      elif self.state == STATE_IP_SENT:
        debug("Processing ip reply")
        self.processStatusResponse(line)

    finally:
      logger.uuid = None

  def processIpRequest(self,line):
    allocator = self.allocator
    try:
      parts = line.split(" ",2)
      if len(parts) != 2:
        error("got invalid line [%s]"%(line))
        self.transport.loseConnection()
        return
      
      domain, email_address = parts
      details = self.allocator.getIpAddress(domain,email_address)
      if details:
        info("Got %s for %s on %s"%(details, email_address, domain)) 
        self.transport.write("%s %s\n"%(details.getIpAddress(),details.getHeloHost()))
        self.email_address = email_address
        self.domain = domain
        self.ip_address = details
        self.state = STATE_IP_SENT
      else:
        warning("No available ip address for %s on %s"%(email_address,domain))
        self.transport.loseConnection()
        self.state = STATE_COMPLETED

    except Exception as e:
      exception(e)
      self.transport.looseConnection()
  
  def processStatusResponse(self,line):
    ip_address = code = message = None
    
    try:
      ip_address, code, message = line.split(" ", 2)
    except Exception as e:
      error("got invalid line [%s] from qmail-remote", line)
      exception(e)
      self.transport.loseConnection()
      return

    code = int(code)
    if code >= 400:
      error("%d %s", code, message)
      self.ip_address.makeBlacklisted()
      self.allocator.invalidateAssociation( self.domain, self.email_address)
      critical("%s has been blacklisted by %s on pool %s", self.ip_address.ip_address, self.email_address, self.domain)
    else:
      info("%d %s", code, message)

    self.transport.loseConnection()

class IpManagerFactory(protocol.Factory):

  def __init__(self,allocator):
    self._allocator = allocator

  def buildProtocol(self, addr):
    return IpManager(self._allocator)
