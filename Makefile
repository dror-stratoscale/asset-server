all: unittest build check_convention

clean:
	sudo rm -fr build images.fortests

UNITTESTS=$(shell find tests -name 'test*.py' | sed 's@/@.@g' | sed 's/\(.*\)\.py/\1/' | sort)
unittest:
	-mkdir build
	PYTHONPATH=. UPSETO_JOIN_PYTHON_NAMESPACES=yes python -m unittest $(UNITTESTS)

check_convention:
	pep8 asset tests --max-line-length=109

.PHONY: build
build: build/asset-server.egg

build/asset-server.egg: asset/server/main.py
	-mkdir $(@D)
	python -m upseto.packegg --entryPoint=$< --output=$@ --createDeps=$@.dep --compile_pyc --joinPythonNamespaces
-include build/asset-server.egg.dep

install: build/asset-server.egg
	-sudo systemctl stop asset-server.service
	-sudo mkdir /usr/share/asset-server
	sudo cp build/asset-server.egg /usr/share/asset-server
	sudo cp asset-server.service /usr/lib/systemd/system/asset-server.service
	sudo systemctl enable asset-server.service
	if ["$(DONT_START_SERVICE)" == ""]; then sudo systemctl start asset-server; fi

uninstall:
	-sudo systemctl stop asset-server
	-sudo systemctl disable asset-server.service
	-sudo rm -fr /usr/lib/systemd/system/asset-server.service
	sudo rm -fr /usr/share/asset-server
