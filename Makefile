.PHONY: install clean uninstall

install:
	@python setup.py install

clean:
	rm -rv build/ dist/ *.egg-info/

uninstall:
	@pip uninstall whcnethelper
