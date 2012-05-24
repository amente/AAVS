import unittest

from aavs import *

class NumberTests(unittest.TestCase):
  def test_roundoff(self):
    answer = Number("11/10")
    self.assertTrue(answer.match("1.1"))
    self.assertFalse(answer.match("1.15"))
    self.assertTrue(answer.match("1.10"))
    self.assertFalse(answer.match("1.11"))
    self.assertFalse(answer.match("21/20"))

    answer = Number("1.39412")
    self.assertFalse(answer.match("1.39", digits=3))
    self.assertTrue(answer.match("1.39", digits=2))
    self.assertTrue(answer.match("1.4", digits=1))

    answer = Number("0")
    self.assertFalse(answer.match("0/0")) # 0/0 is NaN
    self.assertTrue(answer.match("0.000000000001")) # unfortunately, due to rounding.

    answer = Number("1/2", "1")
    self.assertTrue(answer.match("0.7"))
    self.assertFalse(answer.match("0.3"))
    self.assertFalse(answer.match("1.3"))

    self.assertTrue(answer.match("1/2"))
    self.assertTrue(answer.match("1"))

    self.assertTrue(answer.match("0.5", rangemode="inclusive_low"))
    self.assertFalse(answer.match("1", rangemode="inclusive_low"))

    self.assertTrue(answer.match("1", rangemode="inclusive_high"))
    self.assertFalse(answer.match("0.5", rangemode="inclusive_high"))

    self.assertFalse(answer.match("0.5", rangemode="exclusive"))
    self.assertFalse(answer.match("1", rangemode="exclusive"))

class StringTests(unittest.TestCase):
  def test_lower(self):
    answer = String("Test STRING!     ")
    self.assertTrue(answer.match("test string!"))
    self.assertTrue(answer.match("  teSt stRing!  "))
    self.assertFalse(answer.match("test 1string!"))

  def test_exact(self):
    answer = String("Test STRING!     ", match_mode="exact")
    self.assertTrue(answer.match("Test STRING!   "))
    self.assertFalse(answer.match("test string!"))
    self.assertFalse(answer.match("  teSt stRing!  "))
    self.assertFalse(answer.match("test 1string!"))

  def test_pattern(self):
    answer = String("test", match_mode="pattern")
    self.assertTrue(answer.match("TEST"))
    self.assertFalse(answer.match("testl"))

    answer = String("test*", match_mode="pattern")
    self.assertTrue(answer.match("testl"))
    self.assertTrue(answer.match("teSt..** adfkjaldkfja"))
    self.assertFalse(answer.match("adfaf testadfadf"))

  def test_regex(self):
    answer = String("^t[e|a]st$", match_mode="regex")
    self.assertTrue(answer.match("test"))
    self.assertTrue(answer.match("tast"))
    self.assertFalse(answer.match("tfst"))

class MultipleGuessTest(unittest.TestCase):
  def test_exact(self):
    answer = MultipleGuess("0")
    self.assertTrue(answer.match("0"))
    self.assertFalse(answer.match("1"))

  def test_multiple_exact(self):
    answer = MultipleGuess(["0", "1"], match_mode="multiple_exact")
    self.assertTrue(answer.match(["0", "1"]))
    self.assertFalse(answer.match(["0", "1", "2"]))

  def test_include(self):
    answer = MultipleGuess(["0", "1", "2"], match_mode="include")
    self.assertTrue(answer.match("0"))
    self.assertTrue(answer.match(["0", "1"]))
    self.assertTrue(answer.match(["0", "2", "1"]))
    self.assertFalse(answer.match(["0", "1", "2", "3"]))

  def test_exclude(self):
    answer = MultipleGuess(["0", "1"], match_mode="exclude")
    self.assertFalse(answer.match("0"))
    self.assertFalse(answer.match(["0", "1"]))
    self.assertFalse(answer.match(["0", "2", "1"]))
    self.assertTrue(answer.match(["2", "3"]))

class ListOfAnswersTest(unittest.TestCase):
  def test_exact(self):
    answer1 = Number("1/2")
    answer2 = String("km")
    answer = ListOfAnswers([answer1, answer2])

    self.assertTrue(answer.match(["0.5", "KM"]))
    self.assertTrue(answer.match(["1/2", "Km "]))
    self.assertTrue(answer.match(["0.50000001", "km"]))
    self.assertFalse(answer.match(["0.6", "KM"]))
    self.assertFalse(answer.match(["0.5", "KM/s"]))
    self.assertFalse(answer.match(["0.52", "KM/s"]))

  def test_exact_unordered(self):
    answer1 = String("paris")
    answer2 = String("moscow")
    answer = ListOfAnswers([answer1, answer2], match_mode="exact_unordered")

    self.assertTrue(answer.match(["paris", "moscow"]))
    self.assertTrue(answer.match(["moscow", "paris"]))
    self.assertFalse(answer.match(["paris", "moscow", "1"]))
    self.assertFalse(answer.match(["paris"]))

  def test_include(self):
    answer1 = String("moscow")
    answer2 = String("paris")
    answer3 = String("ottawa")
    answer = ListOfAnswers([answer1, answer2, answer3], match_mode="include")

    self.assertTrue(answer.match(["paris"]))
    self.assertFalse(answer.match(["paris"], minimum=2))
    self.assertTrue(answer.match(["paris", "moscow"], minimum=1))
    self.assertTrue(answer.match(["paris", "moscow"]))
    self.assertTrue(answer.match(["paris", "moscow", "ottawa"]))
    self.assertFalse(answer.match(["paris", "moscow", "beijing"]))

    self.assertFalse(answer.match(["paris", "beijing"], minimum=1))

  def test_exclude(self):
    answer1 = String("moscow")
    answer2 = String("paris")
    answer = ListOfAnswers([answer1, answer2], match_mode="exclude")

    self.assertFalse(answer.match(["paris"]))
    self.assertFalse(answer.match(["paris"], minimum=2))
    self.assertFalse(answer.match(["ottawa", "moscow"], minimum=1))
    self.assertTrue(answer.match(["ottawa", "beijing"]))
    self.assertTrue(answer.match(["ottawa"]))
    self.assertFalse(answer.match(["ottawa"], minimum=2))

class MapOfAnswersTest(unittest.TestCase):
  def test_exact(self):

    answer1 = Number("2/3")
    answer2 = Number("1/3")
    answer = MapOfAnswers({"a" : answer1, "b" : answer2})

    self.assertTrue(answer.match({"a" : "2/3", "b" : "0.33333"}))
    self.assertFalse(answer.match({"a" : "2/3"}))

if __name__ == "__main__":
  unittest.main(verbosity=2)
