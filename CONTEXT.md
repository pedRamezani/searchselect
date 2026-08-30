# Context

The ubiquitous language for `searchselect`. This is a glossary, not a spec — no
implementation details, no decisions, no notes-to-self.

## SearchSelect

The widget. A searchable, multi-select picker over a list of strings, rendered in a
notebook and read back from Python.

It is **domain-neutral**: it knows nothing but strings. It is not a column picker, not a
vocabulary browser, not a cohort tool, even though it can be used as any of those. Any
language that presumes a domain — _term_, _variable_, _column_, _code_, _concept_ — is
wrong here.

## Item

One string on offer in a SearchSelect. The unit of everything: the thing displayed in a
row, the thing matched against, the thing chosen.

An item is identified **by its own string value**, not by its position in the list. Two
equal strings are the same item, which is why a SearchSelect holds no duplicates.

Not to be confused with a _row_, which is an item's on-screen presentation and may not
exist at all for an item hidden by the current query.

## Selected

The items a person has explicitly chosen, by ticking them.

Selection is an act of intent. It is not affected by what is currently visible: narrowing
the query does not unselect anything, and an item can be selected while hidden.

## Filtered

The items matching the current query.

This is a **query result**, not a choice — nobody decided it, it fell out of what was
typed. When the query is empty every item matches, so _filtered_ is then the whole list,
never nothing.

_Selected_ and _filtered_ are independent and can disagree freely. Both are legitimate
answers to "which items does this person care about?", arrived at by different means:
one by picking, one by describing. A caller chooses which question they are asking.

## Query

What has been typed into the search box, together with the matching mode
(case-sensitivity, regex). Produces _filtered_ from _items_.

A query is expressed in the language of the kernel, not the browser: a regex query is a
Python regex, and means in the widget exactly what it means in the surrounding code. A
query is therefore something a person can take away with them, in the same way a
_selection_ is.

A query that cannot be parsed — a malformed regex — matches nothing, and says why. It is
not the same as an empty query, which matches everything.

The empty query is the resting state, and it is the reason _filtered_ can always be
answered without asking: everything matches, so the answer is _items_.

## Host

The notebook surface the widget is rendered in: JupyterLab, VS Code, or anything else
that renders anywidget.

The widget is a guest in the host. It adopts the host's typography rather than bringing
its own, confines its styling to itself rather than restyling the host's other output,
and paints only up to its own edge — a surround it did not draw is not its to correct.

A host's theme is inferred, not announced: there is no agreed way to ask. So the
inference can be overridden, and an explicit choice always outranks a guess.
