"""
A Spec is 'what' a user wants marshaled or unmarshaled - not quite 'how', which remains the factories' business. The
common case remains a reflected type, but InternalSpec subclasses are first-class citizens of the factory contract:
factories are given a Spec and pass on those they don't recognize, letting detection ('this reflected type is a
dataclass') be decoupled from construction ('build a handler for this ObjectSpec') - a spec deriving factory resolves a
reflected type to an InternalSpec and re-enters via its context (`return lambda: ctx.make_marshaler(spec)`).

InternalSpecs are values: they must be immutable, hashable, and compare by value - they are their own handler cache keys
(reflected types are keyed by their TypeKey). They are not type-annotation citizens - they cannot appear inside
annotations - but they are accepted anywhere a marshalable target is taken: user entrypoints, vias, and `make_marshaler`
/ `make_unmarshaler` calls.
"""
from ... import lang
from ... import reflect as rfl


##


class InternalSpec(lang.Abstract):
    pass


type Spec = rfl.Type | InternalSpec
