# mysqldump_reformat.py
Script to split enormously long lines made by mysqldump into shorter lines.

"Extended insert" can create lines too long, making importing dump not
possible and resulting in "fake" errors (file is correct, but db engine reads
only as big part of the line as possible and tries to process it, omitting
the other part, frequently braking words or instructions in the middle).
It can be a problem if you can't make new dump without extended inserts
(e.g. db does not exist already) or you don't want to make new dump without
extended inserts (because import is slower). This scipt can solve the problem.

Inspired by: http://blog.lavoie.sl/2014/06/split-mysqldump-extended-inserts.html

Current version is functional enough to do the job in most cases, but is not
optimized, so can use a lot of memory and take a lot of time to finish the job.

Possible enhancements:

- in process_file():
-- readline (one line at a time) instead of readlines, to lower memory usage
-- write (append) processed line into file immediately and free the memory
-- force output file to be different than input file

- in ask_confirmation():
-- use list of allowed answers (e.g. "y", "yes", etc.), not only one option

- in general:
-- use translated strings (localization, e.g. using gettext)
