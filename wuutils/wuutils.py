import csv
import math
import types
from itertools import *
import json
import random
from operator import *
from functools import partial


from pygg import *
from cashier import cache


# Source Sans Pro Light
legend = theme_bw() + theme(**{
  "legend.background": element_blank(), #element_rect(fill=esc("#f7f7f7")),
  "legend.justification":"c(1,0)", "legend.position":"c(1,0)",
  "legend.key" : element_blank(),
  "legend.title":element_blank(),
  "text": element_text(colour = "'#333333'", size=11, family = "'Arial'"),
  "axis.text": element_text(colour = "'#333333'", size=11),  
  "plot.background": element_blank(),
  "panel.border": element_rect(color=esc("#e0e0e0")),
  "strip.background": element_rect(fill=esc("#efefef"), color=esc("#e0e0e0")),
  "strip.text": element_text(color=esc("#333333"))
  
})

# need to add the following to ggsave call:
#    libs=['grid']
legend_bottom = legend + theme(**{
  "legend.position":esc("bottom"),
  #"legend.spacing": "unit(-.5, 'cm')"

})

legend_none = legend + theme(**{"legend.position": esc("none")})




###############################################
#
#  Caching Utilities
#
###############################################
def cacheit(fname="./.cache.db", **kwargs):
  kwargs['cache_file'] = fname
  return cache(**kwargs)



       



###############################################
#
#  Data manipulation utilities
#
###############################################

def replace_attr(data, attr, f, skip_nulls=True):
  """
  equivalent to:
  for d in data:
    if d[attr] != None or not skip_nulls:
      d[attr] = f(d[attr])
  """
  for d in data:
    if attr not in d:
      d[attr] = None
    if d.get(attr, None) != None or not skip_nulls:
      d[attr] = f(d[attr])
  return data

def dedup_list(seq, key=lambda d: d):
  """
  Order preserving dedup
  """
  seen = set()
  seen_add = seen.add
  return [ x for x in seq if not (key(x) in seen or seen_add(key(x)))]

def filter_data(data, *args, **kwargs):
  """
  Filter a list of objects based on attribute's value
  args can be [attr, val] for a single atribute, and value
  kwargs is pairs of attr=val
  """
  tolist = lambda v: isinstance(v, list) and v or [v]
  f = lambda v: True
  h = lambda v: True
  if len(args) >= 2:
    attr, vals = args[0], set(args[1:])
    f = lambda d: d[attr] in vals
  if kwargs:
    h = lambda d: all((d.get(k, None) in tolist(v) for k,v in kwargs.items()))
  return [d for d in data if f(d) and h(d)]

def combine_lists(list_of_lists):
  """
  """
  ret = []
  for l in list_of_lists:
    ret.extend(l)
  return ret

def bucketize(seq, nbuckets, key=lambda d: d):
  """
  Equiwidth bucketing
  Augments _copies_ of objects with the following keys:

    bucket_perc
    bucket_perc_str
    bucket (key value)
    lower (key val)
    upper (key val)


  @param seq a list of objects
  @param key function to compute a numerical value to define bucket sizes
  """
  vals = list(map(key, seq))
  val_range = max(vals) - min(vals)
  bucket_size = int(math.ceil(float(val_range) / nbuckets))
  ret = []
  for i in range(nbuckets):
    l, u = bucket_size * (i), bucket_size * (i+1)
    f = lambda d: key(d) >= l and key(d) < u
    if i == nbuckets - 1:
      f = lambda d: key(d) >= l and key(d) <= u
    for d in filter(f, seq):
      d = dict(d)
      d.update({
        "bucket_perc": int(100. * i / nbuckets),
        "bucket_perc_str": "%d-%d%%" % (int(100. * i / nbuckets),int(100. * (1+i) / nbuckets)),
        "bucket": i,
        "lower": l,
        "upper": u,
      })
      ret.append(d)
  return ret

def plucker(key, default=None):
  """
  return a function that extracts an attribute or a default value
  """
  return lambda d: d.get(key, default)

def pluck(arr, keys):
  ret = []
  for d in arr:
    newd = {}
    for k in keys:
      newd[k] = d.get(k,None)
    ret.append(newd)
  return ret

def pluckone(arr, key):
  return [d.get(key, None)for d in arr]


def fold(data, attrs, keyname="key", valname="val"):
  ret = []
  for d in data:
    for attr in attrs:
      newd = dict()
      newd.update(d)
      newd[keyname] = attr
      newd[valname] = d.get(attr, None)
      ret.append(newd)
  return ret

def split_and_run(l, keys, f):
  """
  keys: attr values to group by on
  f(groupname, items) -> items
  """
  keyf = lambda d: tuple([d[k] for k in keys])
  l = sorted(l, key=keyf)
  ret = []
  for group_id, items in groupby(l, key=keyf):
    item = f(group_id, list(items))
    if isinstance(item, types.GeneratorType):
      item = list(item)
    elif not isinstance(item, list) and not isinstance(item, tuple):
      item = [item]
    ret.extend(item)
  return ret
    


def to_utf(v):
  """
  Do anything under the sun to get a string out of this value.
  """
  if isinstance(v, str):
    s = v.encode('utf-8', errors='ignore')
  elif isinstance(v, str):
    s = str(v, 'utf-8', errors='ignore').encode('utf-8', errors='ignore')
  else:
    s = str(v)
  return s


def sample_pts(pts, perc):
  """
  Non-random deterministic shitty sampler
  """
  i = 0
  foo = []
  while i <= 1.0 and int(i * (len(pts)-1)) < len(pts):
    foo.append(pts[int(i * (len(pts)-1))])
    i += perc
  return foo


def args_to_sql(kwargs):
  l = []
  for k,v in kwargs.items():
    if "." in k:
      k = '"%s"' % k
    if isinstance(v, str):
      v = "'%s'" % v
    elif v == True:
      v = 'true'
    elif v == False:
      v = 'false'
    else:
      v = str(v)
    l.append("%s = %s" % (k, v))
  if not l: 
    return "1 = 1"
  return " AND ".join(l)



def load_csv(fname):
  with file(fname) as f:
    dialect = csv.Sniffer().sniff(f.read(2024))
    f.seek(0)
    reader = csv.reader(f, dialect)
    header = next(reader)
    data = [dict(list(zip(header, l))) for l in reader]
  return data


def run_q(db, q, *args, **kwargs):
  """
  Helper function to turn database query results into list of python dicts
  """
  if args and kwargs:
    cur = db.execute(q, *args, **kwargs)
  elif args:
    cur = db.execute(q, *args)
  elif kwargs:
    cur = db.execute(q, **kwargs)
  else:
    cur = db.execute(q)
  keys = list(cur.keys())
  data = []
  for row in cur:
    data.append(dict(list(zip(keys, list(row)))))
  return data

def data_to_db(db, data, tablename="data"):
  """
  @db database connection
  @data  list of dicts
  @return list of query strings

  Infers schema and loads into a database

  Usage:

      db = create_engine("sqlite://")
      data_to_db(db, data, "data")
  """
  keys = set()
  def gettype(v):
    try:
      int(v)
      return "numeric"
    except: 
      pass
    try:
      float(v)
      return "float"
    except:
      pass
    if v is None or v == "": return None
    return "text"

  def getcoltype(data, key):
    vs = list(filter(bool, pluckone(data, key)))
    types = set(map(gettype, vs))
    #import pdb; pdb.set_trace()
    if not types or "text" in types: 
      return "text"
    if "float" in types:
      return "float"
    if "long" in types or "numeric" in types:
      return "numeric"
    if "int" in types: 
      return "int"
    return "text"
  getcoltype = partial(getcoltype, data)

  for d in data[:10000]:
    keys.update(list(d.keys()))

  ctemplate = "CREATE TABLE IF NOT EXISTS %s(%s)"
  itemplate = "INSERT INTO %s(%s) VALUES(%s)"

  qs = []
  keys = list(keys)
  types = list(map(getcoltype, keys))
  schema = ["%s %s" % (k,t) for k,t in zip(keys, types)]
  q = ctemplate % (tablename, ", ".join(schema))
  qs.append(q)
  db.execute(q)

  # make sure all text types are actually strings
  strkeys = [k for k,t in zip(keys, types) if t == "text"]
  data = list(map(dict, data))
  for d in data:
    for k in strkeys:
      d[k] = str(d.get(k, ''))

  data = [[d.get(k,None) for k in keys] for d in data]
  q = itemplate % (tablename, ", ".join(keys), ", ".join(["?"] * len(keys)))
  qs.append(q)
  db.execute(q, data)

  return qs
