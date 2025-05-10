# t5starshipsim
A discrete-event simulator for starship travel

The Traveller game in all forms is owned by Mongoose Publishing. Copyright 1977 – 2024 Mongoose Publishing. [Fair Use Policy](https://cdn.shopify.com/s/files/1/0609/6139/0839/files/Traveller_Fair_Use_Policy_2024.pdf?v=1725357857)

There is a requirements.txt. I got it like this:
```bash
pip install pipreqs
pipreqs . --force
```

to use it:
```bash
python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
```

then 

```bash
pip install -r requirements.txt
```

The python package's code is in `T5Code` and the tests are in the `tests` directory.

I use black to fix my quotes:
```bash
pip install black
black .
```

To test this code, you can do 
```bash
python -m unittest
```
and then
```bash
coverage run -m unittest discover
coverage report
```
or
`coverage html`
then open file:///htmlcov/index.html in a browser

Looking for TDD'd code, look no further.
```
t5starshipsim % coverage report
Name                    Stmts   Miss  Cover
-------------------------------------------
T5Code/GameState.py       103     80    22%
T5Code/T5Basics.py         18      0   100%
T5Code/T5Lot.py            59      0   100%
T5Code/T5Mail.py           15      0   100%
T5Code/T5NPC.py            18      0   100%
T5Code/T5ShipClass.py      11      0   100%
T5Code/T5Starship.py       98      0   100%
T5Code/T5Tables.py          4      0   100%
T5Code/T5World.py          15      0   100%
T5Code/sim.py             149    149     0%
-------------------------------------------
TOTAL                     490    229    53%
```
There is a test simulator/Game called GameState.py.
Run it like this:
```bash
python GameState.py
```
It outputs a journal of activities taken by one starship.

This code will eventually be used by a simpy discrete-event simulation of thousands of starships in an Imperium.