exports = namespace "aavs"
math = require "math"
# delete above lines if just plugging this file in.
# This is used with coffeecrispt in a namespace or whatever.

# If compiled not with math.coffee, use this function:
# math.roundToDecimalPlace = (v, decimalPlace) ->
#   p = Math.pow(10, decimalPlace)
#   Math.round(v * p) / p


class Answer
  set_match_mode: (match_mode) ->
    @match = this["match_" + match_mode] or this["match_" + @match_methods[0]]
    this

  # differ from python as python takes option=value. This requires an object
  set_options: (options) ->
    originals = @options or {}
    $.extend(originals, options)
    @options = originals

# Javascript took Number. >.>
class ANumber extends Answer
  EXACT: 0
  RANGE: 1

  match_methods: ["roundoff", "sigfig"] # sigfig not available.

  range_checker: {
    inclusive: ((low, v, high) -> low <= v <= high),
    exclusive: ((low, v, high) -> low < v < high),
    inclusive_low: ((low, v, high) -> low <= v < high),
    inclusive_high: ((low, v, high) -> low < v <= high)
  }

  fraction_regex: new RegExp("(-?\\d+)/(\\d+)")
  scinote_regex: new RegExp("([0-9.]+)e([+\\-]?\\d+)")

  set_options: (options) ->
    super(options)
    if "digits" of options
      if $.type(@original) == "string"
        @answer_mode = @EXACT
        @answer = @_interpret_input(@original)
      else
        @answer_mode = @RANGE
        @low = @_interpret_input(@original[0])
        @high = @_interpret_input(@original[1])

  constructor: (answer, match_mode="default", options={}) ->
    @original = answer
    @set_match_mode(match_mode)
    if "digits" not of options
      options["digits"] = 2
    @set_options(options)

  _interpret_input: (answer) ->
    roundoff = @options["digits"] or 2
    if not @fraction_regex.test(answer)
      if not @scinote_regex.test(answer)
        answer = math.roundToDecimalPlace(parseFloat(answer), roundoff)
      else
        m = @scinote_regex.exec(answer)
        base = m[1]
        exponent = m[2]

        if base == null or exponent == null
          return NaN

        answer = base * Math.pow(10, exponent)
    else
      m = @fraction_regex.exec(answer)
      top = m[1]
      bottom = m[2]
      if top == null or bottom == null or bottom == 0
        return NaN

      answer = math.roundToDecimalPlace(top / bottom, roundoff)

    answer


  match_roundoff: (answer) ->
    if @answer_mode == @RANGE
      range_checker = @range_checker[@options["rangemode"] or "inclusive"]
      range_checker(@low, @_interpret_input(answer), @high)
    else
      String(@_interpret_input(answer)) == String(@answer)

  match_sigfig: (answer) -> throw "NOT IMPLEMENTED!"

exports["Answer"] = Answer
exports["ANumber"] = ANumber
