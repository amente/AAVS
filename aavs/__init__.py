import re
import math
from decimal import Decimal

# convention for match_methods is that the default method is on the 0 slot

class Answer(object):
  def set_match_mode(self, match_mode):
    self.match = getattr(self, "match_" + match_mode, getattr(self, "match_" + self.__class__.match_methods[0]))
    return self

class Number(Answer):
  EXACT = 0
  RANGE = 1

  match_methods = ("roundoff", "sigfig")

  range_checker = {
    "inclusive" : lambda low, v, high: low <= v <= high,
    "exclusive" : lambda low, v, high: low < v < high,
    "inclusive_low" : lambda low, v, high: low <= v < high,
    "inclusive_high" : lambda low, v, high: low < v <= high
  }

  def __init__(self, answer, match_mode="default"):
    if isinstance(answer, str):
      self.answermode = Number.EXACT
      self.answer = self._interpret_input(answer)
    else:
      self.answermode = Number.RANGE
      self.low = self._interpret_input(answer[0])
      self.high = self._interpret_input(answer[1])

    self.set_match_mode(match_mode)

  fraction_regex = re.compile("(\d+)/(\d+)", flags=re.U)
  def _interpret_input(self, answer, **kwargs):
    m = Number.fraction_regex.match(answer)
    if m is None:
      answer = Decimal(answer)
    else:
      top, bottom = m.groups()
      if bottom == "0":
        return Decimal("NaN")
      answer = Decimal(top) / Decimal(bottom)

    return answer

  def match_roundoff(self, answer, **kwargs):
    digits = kwargs.get("digits", 2)
    answer = round(self._interpret_input(answer), digits)
    if self.answermode == Number.RANGE:
      low = round(self.low, digits)
      high = round(self.high, digits)
      range_checker = self.range_checker.get(kwargs.get("rangemode", "inclusive"))
      return range_checker(low, answer, high)
    else:
      return str(answer) == str(round(self.answer, digits)) # CODE-REVIEW: Enough? Too much? For ensuring float == float

  def match_sigfig(self, answer):
    raise NotImplementedError # TODO: Implement this

class String(Answer):
  """String answers. Will always strip whitespace."""

  match_methods = ("ignorecase", "exact", "pattern", "regex")

  def __init__(self, answer, match_mode="default"):
    self.set_match_mode(match_mode)
    self.answer = answer.strip()

  def match_ignorecase(self, answer, **kwargs):
    return answer.strip().lower() == self.answer.lower()

  def match_exact(self, answer, **kwargs):
    return answer.strip() == self.answer

  def match_pattern(self, answer, **kwargs):
    temp = self.answer.strip().replace(".", r"\.") # CODE-REVIEW: Again. Auto compilation at init.
    pattern = "^"
    for i, c in enumerate(temp):
      if c == "*" and temp[i-1] != "\\":
        c = ".+"

      pattern += c

    pattern += "$"

    if kwargs.get("ignorecase", True):
      return re.match(pattern, answer.strip(), flags=re.I) is not None
    else:
      return re.match(pattern, answer.strip()) is not None

  def match_regex(self, answer, **kwargs):
    if kwargs.get("ignorecase", True):
      return re.match(self.answer, answer.strip(), flags=re.I) is not None # CODE-REVIEW: Should we somehow compile this before hand for speed up?
    else:
      return re.match(self.answer, answer.strip()) is not None

class MultipleGuess(Answer):
  match_methods = ("exact", "multiple_exact", "include", "exclude")

  def __init__(self, answer, match_mode="default"):
    self.answer = answer
    self.set_match_mode(match_mode)

  def match_exact(self, answer, **kwargs):
    return answer == self.answer

  def match_multiple_exact(self, answer, **kwargs):
    return set(answer) == set(self.answer)

  def match_include(self, answer, **kwargs):
    if isinstance(answer, basestring):
      return answer in self.answer # CODE-REVIEW: Again, should this be a set to start with, or a dict? Reason: Speed.
    else:
      try:
        iter(answer)
      except TypeError:
        return answer in self.answer
      else:
        for a in answer:
          if a not in self.answer:
            return False
        return True

  def match_exclude(self, answer, **kwargs):
    if isinstance(answer, basestring):
      return answer not in self.answer
    else:
      try:
        iter(answer)
      except TypeError:
        return answer not in self.answer
      else:
        for a in answer:
          if a in self.answer:
            return False
        return True

class ListOfAnswers(Answer):
  match_methods = ("exact", "exact_unordered", "include", "exclude")

  def __init__(self, answer, match_mode="default"):
    if len(answer) > 0:
      if isinstance(answer[0], (tuple, list)):
        temp = []
        for clsname, a, match_mode in answer:
          temp.append(globals()[clsname](a, match_mode))
        answer = temp # CODE-REVIEW: Make this simpler. To be compatible

    self.answer = answer
    self.set_match_mode(match_mode)

  def match_exact(self, answer, **kwargs):
    if len(answer) != len(self.answer):
      return False

    for i, a in enumerate(answer):
      if not self.answer[i].match(a):
        return False

    return True

  def match_exact_unordered(self, answer, **kwargs):
    # CODE-REVIEW: Faster method. Current is O(n^2)
    # Does it really matter though? It's not like there are gonna be 100k answers.
    # This maybe improved if the self.answer is somehow used.
    # INVESTIGATE: any(f(v) for v in values for f in functions)?

    if len(answer) != len(self.answer):
      return False

    return all(any(j.match(a) for j in self.answer) for a in answer)

  def match_include(self, answer, **kwargs):
    # INVESTIGATE: match_exclude style optimization
    n = 0
    minimum = kwargs.get("minimum", len(answer))
    for a in answer:
      found = False
      for j in self.answer:
        if j.match(a):
          n += 1
          found = True
          break

      if not found:
        return False

    if n >= minimum:
      return True
    return False

  def match_exclude(self, answer, **kwargs):
    n = 0
    minimum = kwargs.get("minimum", len(answer))

    for a in answer:
      for j in self.answer:
        if j.match(a):
          return False
      n += 1
    if n >= minimum:
      return True
    return False

class MapOfAnswers(Answer):
  match_methods = ("exact", )

  def __init__(self, answer, match_mode="default"):
    if len(answer) > 0:
      if isinstance(answer.values()[0], (tuple, list)):
        temp = {}
        for key, v in answer.iteritems():
          clsname, a, match_mode = v
          temp[key] = globals()[clsname](a, match_mode)
        answer = temp
    self.answer = answer
    self.set_match_mode(match_mode)

  def match_exact(self, answer, **kwargs):
    if len(answer) != len(self.answer):
      return False

    for k, v in answer.iteritems():
      a = self.answer.get(k, None)
      if a is None:
        return False
      if not a.match(v):
        return False

    return True
