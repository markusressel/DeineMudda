# DeineMudda

Nee, deine Mudda!

# Developer docs

## Setup

To install the `pattern` library used by this bot you probably have to 
install `python-mysqlclient` as a system package manually.

## Debugging and execution

Because of [PEP 479](https://www.python.org/dev/peps/pep-0479/) which is
not yet respected in the `pattern` library used by this bot
it is required to use a python 3 runtime lower than 3.7 so 3.6 is 
recommended.

Make sure to use the project base dir as the working directory and run: 
```
python3 ./deinemudda/main.py
```

# Attributions

Thx to @njamster for coming up with the idea and first working version
of this bot.

# Contributing

GitHub is for social coding: if you want to write code, I encourage contributions through pull requests from forks
of this repository. Create GitHub tickets for bugs and new features and comment on the ones that you are interested in.

# License
```text
MIT License

Copyright (c) 2019 Markus Ressel

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```