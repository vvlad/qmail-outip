
from IpAddress import IpAddress

from IpPool import IpPool
from redis import Redis
import logging
import pickle
import hashlib

logger = logging.getLogger("outip")

class MemoryCache(object):

  def __init__(self):
    self.cache = {}

  def set(self, key, value): self.cache[key] = value
  def get(self, key, value): return self.cache[key]

class IpAllocator(object):
  
  DEFAULT_POOL_NAME = "default"

  def __init__(self,config=dict()):
    self.pools = {}
    
    self.initializeRedis(config.get('redis') or dict())
    self.initializeDomains(config.get('domains') or dict())

  def initializeDomains(self,config):
    for pool, spec in config.items(): self.pools[pool] = self.createPool(pool, spec)


  def poolKey(self,name, config): return "pool:%s:versions:%s"%(name, hashlib.sha224(str(config)).hexdigest())

  def createPool(self,name, config):
    key = self.poolKey(name,config); 
    keys = self.redis.keys("pool:%s:*"%(name))
    obj = None

    if not key in keys:
      if len(keys) >0: self.redis.delete(*keys)
      logger.info("Creating new pool for %s"%(name))
      obj = IpPool(name, config)
    
    else:

      old_versions = self.redis.keys("pool:%s:versions:*"%(name))
      old_versions.remove(key)
      if len(old_versions) > 0: self.redis.delete(*old_versions)
      obj = self.getCacheObject(key)

      if obj:
        logger.info("Resuming existing pool for %s"%(name))
      else:
        logger.info("Creating new pool for %s could not resume the old one from the cache"%(name))
        obj = IpPool(name, config)
   
    return obj

  def initializeRedis(self,config):
    self.redis = Redis(
        host = (config.get("hostname") or "localhost"),
        port = int(config.get("port") or 6379),
        db = int(config.get("db") or 0)
    )
    self.ttl = config.get("ttl")
  
  def getIpAddress(self,domain,sender):
    pool = self.getPool(domain)
    key = "pool:%s:association:%s"%(domain,sender)
    record = None
    should_use_cache = pool.isCacheable()

    if should_use_cache: record = self.getCacheObject(key)
    
    if record is None:
      record = pool.nextAddress()
      
      if should_use_cache: record = self.setCacheObject(key, record, self.ttl )
      else: logger.info("Not caching %s on %s due to the fact that %s pool has cache disabled"%(record,domain,pool.getName()))

      self.setCacheObject(self.poolKey(pool.getName(),pool.getConfig()) , pool)
    
    else:
    
      logger.warning("It seems that I wasn't able to figure out an ip address for %s on %s using pool %s"%(sender,domain,pool.getName()))
      logger.debug(pool)

    return record 

  def getCacheObject(self, key):
    
    try:
      data = self.redis.get(key)
      if data is not None: return pickle.loads(self.redis.get(key))
    except Exception as e:
      logger.exception(e)
    
    return None

  def setCacheObject(self, key, value, expire = False):
    
    if value:
      logger.debug("Caching %s"%(key))
      self.redis.set(key, pickle.dumps(value))
      if expire: self.redis.expire(key, expire)
    else:
      self.redis.delete(key)

    return value

  def getPool(self, domain):
    
    pools = self.pools

    if pools.has_key(domain):
      return  pools[domain]
    else:
      return pools[IpAllocator.DEFAULT_POOL_NAME]

