# HackSoc-Imitate

## Introduction
HackSoc-Imitate (or just imitate bot) is a simple imitate bot designed to imitate users on Slack using a markov chain.

The bot was designed for the HackSoc Slack server. You can blame [Sam](https://github.com/sdhand) and [HackSoc](https://hacksoc.org) in general.

## Dependencies

This bot depends on:
- [Markovify](/jsvine/markovify) - to handle the markov chains,
- [Slacksocket](/vektorlab/slacksocket) - to handle Slack communication,
- [Lark](/lark-parser/lark) - to parse bot commands.

You can install these using the `REQUIREMENTS` file with `pip`. This should be as simple as:

```bash
pip install -r REQUIREMENTS
```

You may wish to use a virtual environment to isolate these dependencies from the rest of your machine.

## License
This project is licensed under the BSD 3-Clause license, see [LICENSE](LICENSE) for details.
