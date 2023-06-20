"""
    Dummy conftest.py for ddrmas_python.

    If you don't know what this is for, just leave it empty.
    Read more about conftest.py under:
    - https://docs.pytest.org/en/stable/fixture.html
    - https://docs.pytest.org/en/stable/writing_plugins.html
"""

# import pytest
from ddrmas_python.utils.base_logger import logger

def print_similarities(sim_dict):
    print("Similarities: ")
    logger.info("Similarities: ")
    for lit1, rlits in sim_dict.items():
        for lit2 in rlits:
            if lit1 == lit2: continue
            if sim_dict[lit1][lit2] != 0:
                print(f"theta({str(lit1)}, {str(lit2)}) = {str(sim_dict[lit1][lit2])}")
                logger.info(f"theta({str(lit1)}, {str(lit2)}) = {str(sim_dict[lit1][lit2])}")

