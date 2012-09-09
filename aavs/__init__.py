import re
from decimal import Decimal

# convention for match_methods is that the default method is on the 0 slot

class Answer(object):
  def set_match_mode(self, match_mode):
    self.match = getattr(self, "match_" + match_mode, getattr(self, "match_" + self.__class__.match_methods[0]))
    return self

  def set_options(self, **options):
    originals = getattr(self, "options", {})
    originals.update(options)
    self.options = originals


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

  def set_options(self, **options):
    Answer.set_options(self, **options)
    if "digits" in options:
      if isinstance(self.original, basestring):
        self.answermode = Number.EXACT
        self.answer = self._interpret_input(self.original)
      else:
        self.answermode = Number.RANGE
        self.low = self._interpret_input(self.original[0])
        self.high = self._interpret_input(self.original[1])

  def __init__(self, answer, match_mode="default", **kwargs):
    self.original = answer
    self.set_match_mode(match_mode)
    kwargs.setdefault("digits", 2)
    self.set_options(**kwargs)

  fraction_regex = re.compile(r"(-?\d+)/(\d+)", flags=re.U)
  scinote_regex = re.compile(r"([0-9.]+)e([+\-]?\d+)", flags=re.U)

  def _interpret_input(self, answer):
    roundoff = self.options.get("digits", 2)

    m = Number.fraction_regex.match(answer)
    if m is None:
      m = Number.scinote_regex.match(answer)
      if m is None:
        answer = round(Decimal(answer), roundoff)
      else:
        base, exp = m.groups()
        base = round(Decimal(base), 2)
        answer = float(str(base) + "e" + str(exp))
    else:
      top, bottom = m.groups()
      if bottom == "0":
        return Decimal("NaN")
      answer = round(Decimal(top) / Decimal(bottom), roundoff)

    return answer

  def match_roundoff(self, answer):
    if self.answermode == Number.RANGE:
      range_checker = self.range_checker.get(self.options.get("rangemode", "inclusive"))
      return range_checker(self.low, self._interpret_input(answer), self.high)
    else:
      return str(self._interpret_input(answer)) == str(self.answer)

  def match_sigfig(self, answer):
    raise NotImplementedError # TODO: Implement this

class String(Answer):
  """String answers. Will always strip whitespace."""

  match_methods = ("ignorecase", "exact", "pattern", "regex")

  def set_match_mode(self, match_mode):
    Answer.set_match_mode(self, match_mode)
    if self.match == self.match_pattern:
      temp = self.original.replace(".", r"\.")
      pattern = "^"
      for i, c in enumerate(temp):
        if c == "*" and temp[i-1] != "\\":
          c = ".+"
        pattern += c
      pattern += "$"
      self.answer = pattern
    else:
      self.answer = self.original

  def __init__(self, answer, match_mode="default", **kwargs):
    self.original = answer.strip()
    self.set_match_mode(match_mode) # sets self.answer
    self.options = kwargs

  def match_ignorecase(self, answer):
    return answer.strip().lower() == self.answer.lower()

  def match_exact(self, answer):
    return answer.strip() == self.answer

  def match_pattern(self, answer):
    if self.options.get("ignorecase", True):
      return re.match(self.answer, answer.strip(), flags=re.I) is not None
    else:
      return re.match(self.answer, answer.strip()) is not None

  def match_regex(self, answer):
    if self.options.get("ignorecase", True):
      return re.match(self.answer, answer.strip(), flags=re.I) is not None # CODE-REVIEW: Should we somehow compile this before hand for speed up?
    else:
      return re.match(self.answer, answer.strip()) is not None

class MultipleGuess(Answer):
  match_methods = ("exact", "exact_multiple", "include", "exclude")

  def set_match_mode(self, match_mode):
    Answer.set_match_mode(self, match_mode)
    if self.match == self.match_exact:
      self.answer = self.original
    else:
      self.answer = set(self.original)

  def __init__(self, answer, match_mode="default", **kwargs):
    self.original = answer
    self.set_match_mode(match_mode)
    self.options = kwargs

  def match_exact(self, answer):
    return answer == self.answer

  def match_multiple_exact(self, answer):
    return set(answer) == self.answer

  def match_include(self, answer):
    if isinstance(answer, basestring):
      return answer in self.answer
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

  def match_exclude(self, answer):
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

  def __init__(self, answer, match_mode="default", **kwargs):
    if len(answer) > 0:
      if isinstance(answer[0], (tuple, list)):
        temp = []
        for clsname, a, mm, options in answer:
          temp.append(globals()[clsname](a, mm, **options))
        answer = temp # CODE-REVIEW: Make this simpler. To be compatible

    self.answer = answer
    self.set_match_mode(match_mode)
    self.options = kwargs

  def match_exact(self, answer):
    if len(answer) != len(self.answer):
      return False

    for i, a in enumerate(answer):
      if not self.answer[i].match(a):
        return False

    return True

  def match_exact_unordered(self, answer):
    if len(answer) != len(self.answer):
      return False

    return all(any(j.match(a) for j in self.answer) for a in answer)

  def match_include(self, answer):
    # CODE-REVIEW: match_exclude style code?
    n = 0
    minimum = self.options.get("minimum")
    if minimum is None:
      minimum = len(answer) # since set_options cannot delete.
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

  def match_exclude(self, answer):
    n = 0
    minimum = self.options.get("minimum")
    if minimum is None:
      minimum = len(answer) # since set_options cannot delete.
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

  def __init__(self, answer, match_mode="default", **kwargs):
    if len(answer) > 0:
      if isinstance(answer.values()[0], (tuple, list)):
        temp = {}
        for key, v in answer.iteritems():
          clsname, a, mm, options = v
          temp[key] = globals()[clsname](a, mm, **options)
        answer = temp
    self.answer = answer
    self.set_match_mode(match_mode)
    self.options = kwargs

  def match_exact(self, answer):
    if len(answer) != len(self.answer):
      return False

    for k, v in answer.iteritems():
      a = self.answer.get(k, None)
      if a is None:
        return False
      if not a.match(v):
        return False

    return True
