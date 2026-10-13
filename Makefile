CXX ?= g++

.PHONY: all ripser pith test smoke

all: ripser pith

ripser:
	$(CXX) -std=c++11 -O3 -DNDEBUG third_party/ripser/ripser.cpp -o third_party/ripser/ripser

pith:
	cmake -S src/pith -B src/pith/build -DCMAKE_CXX_COMPILER=$(CXX)
	cmake --build src/pith/build -j

test: pith
	src/pith/build/pith_test

smoke: ripser pith
	python3 benchmarks/generate_datasets.py --sizes 80,200
	python3 benchmarks/run_suite.py --suite smoke
