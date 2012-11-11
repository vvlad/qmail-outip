
from twisted.internet import protocol
from twisted.protocols.basic import LineReceiver
import logging as logger

STATE_NEW = "new"
STATE_IP_SENT = "ip_send"
STATE_COMPLETED = "completed"


class IpManager(LineReceiver):

  delimiter = "\n"
  
  def __init__(self,allocator):
    self.allocator = allocator
    self.state = STATE_NEW

  def connectionMade(self):
    logger.debug("new connection")
  
  def connectionLost(self,reason):
    logger.debug(reason.getErrorMessage())
    reason.cleanFailure()

  def lineReceived(self, line):
    line = line.strip()
    logger.debug("Command received [%s]. State is '%s'"%(line,self.state)) 
    if self.state == STATE_NEW:
      logger.debug("Processing ip request")
      self.processIpRequest(line)
    elif self.state == STATE_IP_SENT:
      logger.debug("Processing ip reply")
      self.processStatusResponse(line)

  def processIpRequest(self,line):
    allocator = self.allocator
    try:
      parts = line.split(" ",2)
      if len(parts) != 2:
        logger.error("got invalid line [%s]"%(line))
        self.transport.loseConnection()
        return
      
      domain, sender = parts
      details = self.allocator.getIpAddress(domain,sender)
      if details:
        logger.debug("Got %s for %s on %s"%(details, sender, domain)) 
        self.transport.write("%s %s\n"%(details.getIpAddress(),details.getHeloHost()))
      else:
        logger.warning("No available ip address for %s on %s"%(sender,domain))
        self.transport.loseConnection()
      
      self.state = STATE_IP_SENT

    except Exception as e:
      logger.exception(e)
      self.transport.looseConnection()
  
  def processStatusResponse(self,line):
    self.transport.loseConnection()


class IpManagerFactory(protocol.Factory):

  def __init__(self,allocator):
    self._allocator = allocator

  def buildProtocol(self, addr):
    return IpManager(self._allocator)
