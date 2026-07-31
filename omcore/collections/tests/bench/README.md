# Collection benchmarks

Run the complete suite with:

```bash
./python -m omcore.collections.tests.bench
```

The default sizes are 10, 100, 1,000, and 10,000 items. Interface suites compose through their parent interfaces, so
selecting `persistent_mapping` also runs the `mapping` and `collection` workloads:

```bash
./python -m omcore.collections.tests.bench --suite persistent_mapping --sizes 10,100 --fast
./python -m omcore.collections.tests.bench --implementation btree-map --runtime-only
./python -m omcore.collections.tests.bench -k getitem_hit --csv
./python -m omcore.collections.tests.bench --list
```

Runtime rows use the minimum and median of several batches and report time per logical method call or processed item.
An `!` marks a max/min spread above 1.5. Memory rows use `tracemalloc`: `construct` reports the retained footprint of a
new collection, while other rows exclude their prepared input and report allocations retained or peaked by the
operation itself. Object-key implementations use shared weak-referenceable benchmark keys; other implementations use
integer keys.
