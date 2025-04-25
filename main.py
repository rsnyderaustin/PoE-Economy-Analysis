
import logging
import os

from trade_api import StatEnumBuilder

logging.basicConfig(level=logging.INFO)

def generate_enum_stub(text):

    with open("stat_enum.py", "w") as f:
        f.write(text)

print(os.getcwd())
text = StatEnumBuilder.create_enum_file_text()

generate_enum_stub(text=text)
x=0

