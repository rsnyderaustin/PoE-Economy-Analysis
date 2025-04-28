import logging

from compiled_data import ApisCompiler

logging.basicConfig(level=logging.INFO)

compiler = ApisCompiler.compile()
