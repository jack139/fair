PY = python -m compileall -q -f

CONFIG = config

SRC = src
SRC_CONF = $(SRC)/$(CONFIG)

TARGETS = fair
TARGET_CONF = $(TARGETS)/$(CONFIG)

all: clean $(TARGETS)

$(TARGETS):
	cp -r $(SRC) $(TARGETS)
	cat $(TARGETS)/app_helper.py $(TARGETS)/app_settings_test.py > $(TARGETS)/app_helper_test.py
	cat $(TARGETS)/app_settings.py >> $(TARGETS)/app_helper.py
	-$(PY) $(TARGETS)
	find $(TARGETS) -name '*.py' -delete
	rm $(TARGET_CONF)/setting.pyc
	rm $(TARGETS)/app_settings.pyc
	cp $(SRC_CONF)/setting.py $(TARGET_CONF)

clean: 
	rm -rf $(TARGETS)
