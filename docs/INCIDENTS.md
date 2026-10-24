# Incidents (2026-10-21/22) and what would have prevented them

A two-agent repo (fable: lead; opus: builder), one author. Each row: what
happened, how it was caught, and the mechanism that makes it impossible
rather than merely unlikely. Candidate requirements for jack/assize.

| # | incident | caught by | preventing mechanism |
|---|---|---|---|
| 1 | CI red on master for 17 pushes (shallow checkout broke a git-history test); both agents only ran the kit locally | fable, late | a monitor that blocks the next push while master is red; the watcher checks CI per push |
| 2 | `check.sh \| tail -1 && git commit` committed with a red kit (pipe status) | CI, next push | commit gated on the kit's own exit status, in a hook, not a habit |
| 3 | Author's email sent in an API User-Agent | opus, self-reported | outgoing-request policy in the instrument layer (allowlisted headers; no personal data) |
| 4 | Parameters pinned before an amendment landed; one evaluation grid read under the old pin | fable's diff check | pre-registration as an entry: evaluation refuses to run unless the pinned parameters' commit is newer than the brief's last amendment |
| 5 | Brief specs wrong twice (final-state calibration applied mid-run; a bar incompatible with its own threshold) | negative result; then opus before spend | a "decision-rule sanity" check in the brief template: does the rule's success case exist under the stated model? |
| 6 | Answer extraction took a reasoning model's first line; every Sonnet sample scored 0 | smoke test | smoke tests mandatory before paid runs (already practice); structured output by default |
| 7 | Upstream table entries with fused values made "mechanical" steps unsound | fable review | tables are data with origin tags; only reviewed entries count as mechanical |
| 8 | Conflicting authority: the author told the builder to wait for him on spend after delegating spend to the lead | opus asked | explicit precedence: a direct instruction to an agent outranks a delegation until revoked; delegations are entries with scope |
| 9 | Two answers under the wrong QUESTIONS item (formatting slip) | fable, next read | one entry per answer keyed to the question id, not prose placement |
| 10 | Unverified commits (non-noreply author) on pushed history | stop hook | identity set per agent at clone time |
| 11 | Spend guard checked per call with 8 calls in flight: 018's run passed its $11.50 guard by $2.71 (still inside the cap, because the lead had raised it) | opus, in the report | a guard that reserves each in-flight call's projected cost before launching the next, so the sum of launched work never exceeds the guard; CI test on the instrument layer |
| 12 | Two of the lead's pushes went out on top of a red commit: the kit was run before the rebase, not after | CI | run the kit after `pull --rebase` and before `push`, in a hook; a red result on the rebased head blocks the push |
