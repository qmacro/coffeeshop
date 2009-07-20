# Random collection of utils to be assimilated somewhere better soon
import datetime

def agoify(then):
  """See http://stackoverflow.com/revisions/118569/list
  and look for the deliberate(?) mistake there
  """
  diff = datetime.datetime.now() - then
  seconds = diff.seconds
  if seconds < 30:
    return "just now"
  elif seconds < 60:
    return "less than a minute ago"
  minutes = seconds / 60
  if minutes == 1:
    return "a minute ago"
  elif minutes < 60:
    return "%s minutes ago" % (minutes, )
  hours = minutes / 60
  if hours == 1:
    return "an hour ago"
  elif hours < 24:
    return "%s hours ago" % (hours, )
  days = hours / 24
  if days < 2:
    return "yesterday"
  elif days < 30:
    return "%s days ago" % (days, )
# Hmm accuracy--
  months = days / 30
  if months <= 1:
    return "a month ago"
  years = months / 12
  if years < 1:
    return "%s months ago" % (months, )
  elif years == 1:
    return "a year ago"
  return "%s years ago" % (years, )

