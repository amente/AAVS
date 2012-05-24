import re
import math
from decimal import Decimal, getcontext

# convention for match_methods is that the default method is on the 0 slot

class Answer(object):
  def set_match_mode(self, default):
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

  def __init__(self, low, high=None, match_mode="roundoff", range_mode="inclusive"):
    if high is None:
      self.answermode = Number.EXACT
      self.answer = self._interpret_input(lowrange)
    else:
      self.answermode = Number.RANGE
      self.low = self._interpret_input(low)
      self.high = self._interpret_input(high)

    self.set_range_mode(range_mode)
    self.set_match_mode(match_mode)

  def set_range_mode(self, range_mode):
    self.range_checker = self.__class__.range_checker[range_mode]
    return self

  fraction_regex = re.compile("(\d+)/(\d+)", flags=re.U)
  def _interpret_input(self, answer, **kwargs):
    m = Number.fraction_regex.match(answer)
    if m is None:
      answer = Decimal(answer)
    else:
      top, bottom = m.groups()
      answer = Decimal(top) / Decimal(bottom)

    return answer

  def match_roundoff(self, answer, **kwargs):
    digits = kwargs.get("digits", 2)
    answer = round(self._interpret_input(answer), digits)
    if self.answermode == Number.RANGE:
      low = round(self.low, digits)
      high = round(self.high, digits)
      return self.range_checker(low, answer, high)
    else:
      return str(answer) == str(round(self.answer, digits)) # CODE-REVIEW: Enough? Too much? For ensuring float == float

  def match_sigfig(self, answer):
    raise NotImplementedError # TODO: Implement this

class String(Answer):
  """String answers. Will always strip whitespace."""

  match_methods = ("lower", "exact", "regex")

  def __init__(self, answer, match_mode="lower"):
    self.set_match_mode(match_mode)
    self.answer = answer.strip()

  def match_lower(self, answer, **kwargs):
    return answer.strip().lower() == self.answer.lower()

  def match_exact(self, answer, **kwargs):
    return answer.strip() == self.answer

  def match_regex(self, answer, **kwargs):
    return re.match(self.answer, answer.strip()) is not None # CODE-REVIEW: Should we somehow compile this before hand for speed up?

class MultipleGuess(Answer):
  match_method = ("exact", "multiple_exact", "include", "exclude")

  def __init__(self, answer, match_mode="exact"):
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
            return True
        return False

class ListOfAnswers(Answer):
  match_method = ("exact", "exact_unordered", "include", "exclude")

  def __init__(self, answer, match_mode="exact"):
    """Initializes a new list of answers

    Args:
      """
    self.answer = answer
    self.set_match_mode(match_mode)

  def match_exact(self, answer, **kwargs):
    pass

  def match_exact_unordered(self, answer, **kwargs):
    pass

  def match_include(self, answer, **kwargs):
    pass

  def match_exclude(self, answer, **kwargs):
    pass


class MapOfAnswers(Answer):
  pass
