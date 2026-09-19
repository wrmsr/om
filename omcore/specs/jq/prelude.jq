# Adapted from jq 1.8.2 src/builtin.jq.
# jq is Copyright (C) 2012 Stephen Dolan and distributed under the MIT license in LICENSE.
# Recursive repeat/while/until/recurse and tostream are deliberately native in this implementation.

def map(f): [.[] | f];
def select(f): if f then . else empty end;
def sort_by(f): _sort_by_impl(map([f]));
def group_by(f): _group_by_impl(map([f]));
def unique_by(f): _unique_by_impl(map([f]));
def max_by(f): _max_by_impl(map([f]));
def min_by(f): _min_by_impl(map([f]));
def sort: sort_by(.);
def group_by(f): _group_by_impl(map([f]));
def unique: unique_by(.);
def min: min_by(.);
def max: max_by(.);
def add(f): reduce f as $x (null; . + $x);
def add: add(.[]);
def del(f): delpaths([path(f)]);
def abs: if . < 0 then -. else . end;
def map_values(f): .[] |= f;

def to_entries: [keys_unsorted[] as $k | {key: $k, value: .[$k]}];
def from_entries: map({(.key // .Key // .name // .Name):
  if has("value") then .value else .Value end}) | add // {};
def with_entries(f): to_entries | map(f) | from_entries;

def index($i): indices($i) | .[0];
def rindex($i): indices($i) | .[-1];
def paths: path(recurse) | select(length > 0);
def paths(node_filter): path(recurse | select(node_filter)) | select(length > 0);

def arrays: select(type == "array");
def objects: select(type == "object");
def iterables: select(type | . == "array" or . == "object");
def booleans: select(type == "boolean");
def numbers: select(type == "number");
def strings: select(type == "string");
def nulls: select(. == null);
def values: select(. != null);
def scalars: select(type | . != "array" and . != "object");

def join($x): reduce .[] as $i (null;
  (if . == null then "" else . + $x end) +
  ($i | if type == "boolean" or type == "number" then tostring else . // "" end)
) // "";

def _flatten($depth): reduce .[] as $item ([];
  if ($item | type) == "array" and $depth != 0
  then . + ($item | _flatten($depth - 1))
  else . + [$item]
  end);
def flatten($depth):
  if $depth < 0 then error("flatten depth must not be negative") else _flatten($depth) end;
def flatten: _flatten(-1);
def range($end): range(0; $end);

def ltrimstr($left): if startswith($left) then .[$left | length:] else . end;
def rtrimstr($right): if endswith($right) then .[:length - ($right | length)] else . end;
def trimstr($value): ltrimstr($value) | rtrimstr($value);

def match(regex; mode): _match_impl(regex; mode; false) | .[];
def match($value): ($value | type) as $value_type |
  if $value_type == "string" then match($value; null)
  elif $value_type == "array" and ($value | length) > 1 then match($value[0]; $value[1])
  elif $value_type == "array" and ($value | length) > 0 then match($value[0]; null)
  else error($value_type + " is not a string or array")
  end;
def test(regex; mode): _match_impl(regex; mode; true);
def test($value): ($value | type) as $value_type |
  if $value_type == "string" then test($value; null)
  elif $value_type == "array" and ($value | length) > 1 then test($value[0]; $value[1])
  elif $value_type == "array" and ($value | length) > 0 then test($value[0]; null)
  else error($value_type + " is not a string or array")
  end;
def capture(regex; mode): match(regex; mode) |
  reduce (.captures[] | select(.name != null) | {(.name): .string}) as $pair ({}; . + $pair);
def capture($value): ($value | type) as $value_type |
  if $value_type == "string" then capture($value; null)
  elif $value_type == "array" and ($value | length) > 1 then capture($value[0]; $value[1])
  elif $value_type == "array" and ($value | length) > 0 then capture($value[0]; null)
  else error($value_type + " is not a string or array")
  end;
def scan($regex; $flags):
  match($regex; "g" + $flags) |
  if (.captures | length) > 0 then [.captures[].string] else .string end;
def scan($regex): scan($regex; "");

def limit($count; expression):
  if $count > 0
  then label $out |
    foreach expression as $item ($count; . - 1;
      $item, if . <= 0 then break $out else empty end)
  elif $count == 0 then empty
  else error("limit doesn't support negative count")
  end;
def skip($count; expression):
  if $count > 0
  then foreach expression as $item ($count; . - 1; if . < 0 then $item else empty end)
  elif $count == 0 then expression
  else error("skip doesn't support negative count")
  end;
def first(generator): label $out | generator | ., break $out;
def last(generator): reduce generator as $item (null; $item);
def isempty(generator): first((generator | false), true);
def all(generator; condition): isempty(generator | condition and empty);
def any(generator; condition): isempty(generator | condition or empty) | not;
def all(condition): all(.[]; condition);
def any(condition): any(.[]; condition);
def all: all(.[]; .);
def any: any(.[]; .);
def nth($index; generator):
  if $index < 0 then error("nth doesn't support negative indices")
  else first(skip($index; generator))
  end;
def first: .[0];
def last: .[-1];
def nth($index): .[$index];

def inputs: try repeat(input) catch if . == "break" then empty else error end;
def ascii_downcase:
  explode | map(if 65 <= . and . <= 90 then . + 32 else . end) | implode;
def ascii_upcase:
  explode | map(if 97 <= . and . <= 122 then . - 32 else . end) | implode;

def truncate_stream(stream):
  . as $count | null | stream | . as $input |
  if (.[0] | length) > $count then setpath([0]; $input[0][$count:]) else empty end;
def fromstream(stream): {x: null, emit: false} as $initial |
  foreach stream as $item ($initial;
    if .emit then $initial else . end |
    if ($item | length) == 2
    then .emit = (($item[0] | length) == 0) | .x = (.x | setpath($item[0]; $item[1]))
    else .emit = (($item[0] | length) == 1)
    end;
    if .emit then .x else empty end);

def walk(f):
  def w:
    if type == "object" then map_values(w)
    elif type == "array" then map(w)
    else .
    end | f;
  w;
