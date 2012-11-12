
import logging
import sys
logger = logging.getLogger("outip")
from time import asctime
import traceback

logging.basicConfig(format="%(time)s %(level)c:%(where)s:%(line)s%(uuid)s %(message)s",
    level = logging.DEBUG)


logger = logging.getLogger("outip")

def warning(message,*args, **kwargs): log("warning", message, *args, **kwargs)
def error(message,*args, **kwargs): log("error", message, *args, **kwargs)
def debug(message,*args, **kwargs): log("debug", message, *args, **kwargs)
def info(message,*args, **kwargs): log("info", message, *args, **kwargs)
def critical(message,*args, **kwargs): log("critical", message, *args, **kwargs)
def exception(message,*args, **kwargs): log("exception", message, *args, **kwargs)


def log(level,message,*args,**kwargs):
  if level == "exception": level = "error"
  method = getattr(logger, level)
  data = traceback.extract_stack()[-3]
  parts = data[0].split("qmail_outip/")
  where = parts[-1]
  if len(parts)>1: where = ".../qmail_outip/%s"%(where)

  uuid = None
  try:
    uuid = getattr(logger,'uuid')
    if uuid is not None: uuid = ":" + uuid
  except:
    pass
  
  uuid = uuid or ""
  kwargs.update({
    "extra" : {
      "time"  : asctime(),
      "func"  : data[2],
      "line"  : data[1],
      "where" : where,
      "uuid"  : uuid,
      "level" : str(level[0]).upper()
    }
  })
  method(message,*args,**kwargs)
  pass
