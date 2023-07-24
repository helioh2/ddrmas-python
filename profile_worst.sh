python -m cProfile -o myLog.profile ./tests/test_worst_system_bikakis.py 
gprof2dot -f pstats myLog.profile -o callingGraph.dot
dot -Tsvg callingGraph.dot -o callingGraph.svg