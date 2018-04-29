import csv
import math
import types
from itertools import *
import json
import random
from operator import *
from pygg import *


# Source Sans Pro Light
legend = theme_bw() + theme(**{
  "legend.background": element_blank(), #element_rect(fill=esc("#f7f7f7")),
  "legend.justification":"c(1,0)", "legend.position":"c(1,0)",
  "legend.key" : element_blank(),
  "legend.title":element_blank(),
  "text": element_text(colour = "'#333333'", family = esc("Arial"), size=11),
  "axis.text": element_text(colour = "'#333333'", family = esc("Arial"), size=11),  
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
def cacheit(fname="./.cache.db"):
  import bsddb3
  db = bsddb3.hashopen(fname)
  def dec(func):
    def f(*args, **kwargs):
      data = dict(
          name=func.__name__,
          args=args,
          kwargs=kwargs
      )
      key = str(data)
      if key not in db: 
        db[key] = json.dumps(func(*args, **kwargs))
      return json.loads(db[key])
    return f
  return dec



       



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
    if d[attr] != None or not skip_nulls:
      d[attr] = f(d[attr])
  return data

def dedup_list(seq, key=lambda d: d):
  """
  Order preserving dedup
  """
  seen = set()
  seen_add = seen.add
  return [ x for x in seq if not (key(x) in seen or seen_add(key(x)))]

def filter_data(data, attr, val):
  """
  Filter a list of objects based on attribute's value
  """
  return [d for d in data if d[attr] == val]

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
  vals = map(key, seq)
  val_range = max(vals) - min(vals)
  bucket_size = int(math.ceil(float(val_range) / nbuckets))
  ret = []
  for i in xrange(nbuckets):
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
  if isinstance(v, unicode):
    s = v.encode('utf-8', errors='ignore')
  elif isinstance(v, basestring):
    s = unicode(v, 'utf-8', errors='ignore').encode('utf-8', errors='ignore')
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
  for k,v in kwargs.iteritems():
    if "." in k:
      k = '"%s"' % k
    if isinstance(v, basestring):
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
    header = reader.next()
    data = [dict(zip(header, l)) for l in reader]
  return data
