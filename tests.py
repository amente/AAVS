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

    answer = Number("1.39412", digits=3)
    self.assertFalse(answer.match("1.39"))
    answer.set_options(digits=2)
    self.assertTrue(answer.match("1.39"))
    answer.set_options(digits=1)
    self.assertTrue(answer.match("1.4"))

    answer = Number("0")
    self.assertFalse(answer.match("0/0")) # 0/0 is NaN
    self.assertTrue(answer.match("0.000000000001")) # unfortunately, due to rounding.

    answer = Number("-18.292334140232416")
    self.assertTrue(answer.match("-18.29"))
    self.assertFalse(answer.match("18.29"))
    self.assertFalse(answer.match("-18.28"))
    self.assertFalse(answer.match("-18.295"))

    answer = Number(("1/2", "1"))
    self.assertTrue(answer.match("0.7"))
    self.assertFalse(answer.match("0.3"))
    self.assertFalse(answer.match("1.3"))

    self.assertTrue(answer.match("1/2"))
    self.assertTrue(answer.match("1"))

    answer.set_options(rangemode="inclusive_low")
    self.assertTrue(answer.match("0.5"))
    self.assertFalse(answer.match("1"))

    answer.set_options(rangemode="inclusive_high")
    self.assertTrue(answer.match("1"))
    self.assertFalse(answer.match("0.5"))

    answer.set_options(rangemode="exclusive")
    self.assertFalse(answer.match("0.5"))
    self.assertFalse(answer.match("1"))

  def test_scinotation(self):
    answer = Number("9.11e-31")
    self.assertTrue(answer.match("9.11e-31"))
    self.assertTrue(answer.match("9.111e-31"))
    self.assertFalse(answer.match("9.11e+31"))

    answer = Number("9.0e+9")
    self.assertTrue(answer.match("9e9"))
    self.assertTrue(answer.match("9.0e+9"))
    self.assertTrue(answer.match("9.0e9"))
    self.assertTrue(answer.match("9.000e9"))
    self.assertTrue(answer.match("9.001e+9"))
    self.assertFalse(answer.match("9.1e+9"))
    self.assertFalse(answer.match("9.1e+8"))
    self.assertFalse(answer.match("9.1"))

    answer = Number("1.32819375618e231")
    self.assertTrue(answer.match("1.33e231"))

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

    answer = String(r"test\*", match_mode="pattern")
    self.assertTrue(answer.match("test*"))
    self.assertFalse(answer.match("testadf"))

    answer = String("test.", match_mode="pattern")
    self.assertTrue(answer.match("test."))
    self.assertFalse(answer.match("test"))

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

  def test_exact_multiple(self):
    answer = MultipleGuess(["0", "1"], match_mode="exact_multiple")
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
    answer = ListOfAnswers([("Number", "1/2", "default", {}), ("String", "km", "default", {})])

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
    answer.set_options(minimum=2)
    self.assertFalse(answer.match(["paris"]))
    answer.set_options(minimum=1)
    self.assertTrue(answer.match(["paris", "moscow"]))
    answer.set_options(minimum=None)
    self.assertTrue(answer.match(["paris", "moscow"]))
    self.assertTrue(answer.match(["paris", "moscow", "ottawa"]))
    self.assertFalse(answer.match(["paris", "moscow", "beijing"]))
    answer.set_options(minimum=1)
    self.assertFalse(answer.match(["paris", "beijing"]))

  def test_exclude(self):
    answer1 = String("moscow")
    answer2 = String("paris")
    answer = ListOfAnswers([answer1, answer2], match_mode="exclude")

    self.assertFalse(answer.match(["paris"]))
    answer.set_options(minimum=2)
    self.assertFalse(answer.match(["paris"]))
    answer.set_options(minimum=1)
    self.assertFalse(answer.match(["ottawa", "moscow"]))
    answer.set_options(minimum=None)
    self.assertTrue(answer.match(["ottawa", "beijing"]))
    self.assertTrue(answer.match(["ottawa"]))
    answer.set_options(minimum=2)
    self.assertFalse(answer.match(["ottawa"]))

class MapOfAnswersTest(unittest.TestCase):
  def test_exact(self):
    answer = MapOfAnswers({"a" : ("Number", "2/3", "default", {}), "b" : ("Number", "1/3", "default", {})})

    self.assertTrue(answer.match({"a" : "2/3", "b" : "0.33333"}))
    self.assertFalse(answer.match({"a" : "2/3"}))

if __name__ == "__main__":
  unittest.main(verbosity=2)
