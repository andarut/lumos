venv:
	rm -rf .venv && python3.12 -m venv .venv
	.venv/bin/pip3 install -r requirements.txt
	python3.12 -m pip install -r requirements.txt --break-system-packages

demo:
	rm -rf ./build && mkdir ./build
	./.venv/bin/cython ./demo.py --embed --3str -o ./build -M
	gcc	 -O3 $$(python3.12-config --includes) ./build/demo.c \
		-o ./build/demo $$(python3.12-config --ldflags) \
		-l python$$(.venv/bin/python3.12 \
		-c 'import sys; print(".".join(map(str, sys.version_info[:2])))') \
		$$(python3.12-config --abiflags)

debug:
	./.venv/bin/python3 demo.py
