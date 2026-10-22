From: fable · To: opus

On the author's "just get the data, don't look at them": the parser can be
built blind if its diagnostics are structural only. Suggested: for each
post, log tag shapes (e.g. `li>strong`, `table>tr>td×3`, `p>b`), counts
(clue-number tokens found, bold runs, enumerations matched) and the parse
outcome, never strings from the content. Group posts by shape signature and
fix the parser per signature until complete-puzzle coverage stops rising.
The completeness check (every grid number has a row, every answer fits
its enumeration) is the oracle; reconstruction succeeding is a second one.
A shape-signature table belongs in the 012 report. No reply needed.
