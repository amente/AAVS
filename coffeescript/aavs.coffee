# Copyright 2012 Project K3
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Authors:
#   Shuhao Wu <shuhao@projectk3.com>

# Required functions/classes
roundToDecimalPlace = (v, decimalPlace) ->
  p = Math.pow(10, decimalPlace)
  Math.round(v * p) / p

class Set
  constructor: (l) ->
    @_data = {}

    if l
      ltype = $.type(l)
      if ltype == "array"
        for element in l
          @_data[element] = true

      else if ltype == "object"
        for key of l
          @_data[key] = true


  equals: (other) ->
    if other instanceof Set
      for key of other._data
        if key not of @_data
          return false
      true
    else
      @equals(new Set(other))

  has: (value) -> value of @_data

# Actual code for AAVS
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

  match_methods: ["roundoff", "sigfig"] # TODO: sigfig not available

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
        answer = roundToDecimalPlace(parseFloat(answer), roundoff)
      else
        m = @scinote_regex.exec(answer)
        base = roundToDecimalPlace(parseFloat(m[1]), roundoff)
        exponent = parseFloat(m[2])

        if base == null or exponent == null
          return NaN

        answer = base * Math.pow(10, exponent)
    else
      m = @fraction_regex.exec(answer)
      top = m[1]
      bottom = m[2]
      if top == null or bottom == null or bottom == 0
        return NaN

      answer = roundToDecimalPlace(top / bottom, roundoff)

    answer


  match_roundoff: (answer) ->
    if @answer_mode == @RANGE
      range_checker = @range_checker[@options["rangemode"] or "inclusive"]
      range_checker(@low, @_interpret_input(answer), @high)
    else
      String(@_interpret_input(answer)) == String(@answer)

  match_sigfig: (answer) -> throw "NOT IMPLEMENTED!"

class AString extends Answer
  match_methods: ["ignorecase", "exact", "pattern", "regex"]

  set_match_mode: (match_mode) ->
    super(match_mode)
    if @match == @match_pattern
      temp = @original.replace(".", "\\.")
      pattern = "^"
      for c, i in temp
        if c == "*" and temp[i-1] != "\\"
          c = ".+"

        pattern += c
      pattern += "$"
      @answer = pattern
    else
      @answer = @original

  constructor: (answer, match_mode="default", options={}) ->
    @original = $.trim(answer)
    @set_match_mode(match_mode)
    @options = options

  match_ignorecase: (answer) -> $.trim(answer).toLowerCase() == @answer.toLowerCase()

  match_exact: (answer) -> $.trim(answer) == @answer

  match_pattern: (answer) ->
    if @options["ignorecase"] in [true, undefined]
      new RegExp(@answer, "i").test(answer)
    else
      new RegExp(@answer).test(answer)

  match_regex: @prototype.match_pattern

class MultipleGuess extends Answer
  match_methods: ["exact", "exact_multiple", "include", "exclude"]

  set_match_mode: (match_mode) ->
    super(match_mode)
    if @match == @match_exact
      @answer = @original
    else
      @answer = new Set(@original)

  constructor: (answer, match_mode="default", options={}) ->
    @original = answer
    @set_match_mode(match_mode)
    @options = options

  match_exact: (answer) -> @answer == answer
  match_exact_multiple: (answer) -> @answer.equals(answer)
  match_include: (answer) ->
    if $.type(answer) == "string"
      @answer.has(answer)
    else
      for a in answer
        if not @answer.has(a)
          return false
      true

  match_exclude: (answer) ->
    if $.type(answer) == "string"
      not @answer.has(answer)
    else
      for a in answer
        if @answer.has(a)
          return false
      true
