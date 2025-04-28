
import re


# Normalizes mod cleaning across all sources
def format_item_mod(mod_text):
    mod_text = mod_text.strip(' ')
    mod_text = re.sub(r'([+-])(?=#)', '', mod_text)
    return mod_text
