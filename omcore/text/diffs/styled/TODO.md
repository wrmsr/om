# styled diffs

- wrapping: an option to wrap long lines onto continuation rows instead of truncating them
  - the unified layout first - each line already has the full width, so a wrapped line is a plain run of rows
  - continuation rows keep the line's background and intraline ranges, under a blank gutter
  - the split layout needs both halves of an aligned row wrapped to the taller of the two, padding the shorter
