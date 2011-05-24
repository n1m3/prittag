Nero Chapter Format
===================

In the udta (user data) atom there is the chpl (chapter list) atom,
which is structured like the following:
(each number is a 32 bit unsigned integer)
> [Reserved block (set to 1)][number of chapters][start position of chapter one in 100 nanosecond units][Length of the first chapter's name][The first chapter's name][start position of chapter two ]...

