# must use system python
PYTHON := /usr/bin/python3

# get the version number
WF_VERSION := $(shell $(PYTHON) src/__version__.py)

# plist values
WF_NAME := alfred-git-repos
WF_CREATEDBY := deanishe
WF_BUNDLEID := com.${WF_CREATEDBY}.${WF_NAME}
WF_DISABLED := false
WF_WEBADDRESS := github.com/${WF_CREATEDBY}
WF_README := README.md
WF_DESCRIPTION := ""

# resulting workflow to build/install
WF_OUTPUT := ${WF_NAME}-${WF_VERSION}.alfredworkflow


# src/build dirs
SRC_DIR := src
BUILD_DIR := build

.PHONY: build
.PHONY: src-build

all: clean install

# install src/.site-packages
src: requirements.txt
src: PACKAGES=-r requirements.txt
src: src-build

# install bin/.site-packages
bin: PACKAGES=pip-tools==5.5.0
bin: bin/.site-packages

pip-compile: bin

# compile the requirements dir
requirements.txt: pip-compile requirements.in
	PYTHONPATH=./bin/.site-packages:${PYTHONPATH} \
		./bin/.site-packages/bin/pip-compile \
		requirements.in

%/.site-packages:
	# must use the system python
	$(PYTHON) -m pip install \
		--prefer-binary \
		--upgrade \
		--target=$@ \
		${PACKAGES}

src-build:
	# must use the system python
	$(PYTHON) -m pip install \
		--upgrade \
		--target="$(BUILD_DIR)" \
		${PACKAGES}
	rm -rf ./build/*.egg-info ./build/*.dist-info

build: $(WF_OUTPUT)

${WF_NAME}%.alfredworkflow: src
	rsync --archive --verbose \
		--filter '- *.pyc' \
		--filter '- *.egg-info' \
		--filter '- *.dist-info' \
		--filter '- __pycache__' \
		"$(SRC_DIR)/" "$(BUILD_DIR)/"

	./bin/workflow-build \
		--force --verbose \
		--name="${WF_NAME}" \
		--version="${WF_VERSION}" \
		--createdby="${WF_CREATEDBY}" \
		--bundleid="${WF_BUNDLEID}" \
		--disabled="${WF_DISABLED}" \
		--webaddress="${WF_WEBADDRESS}" \
		--readme="${WF_README}" \
		--description="${WF_DESCRIPTION}" \
		"$(BUILD_DIR)" 

	echo "done"

install: $(WF_OUTPUT)
	open $(WF_OUTPUT)

clean:
	rm -rf \
		requirements.txt \
		./build/ \
		.mypy_cache/ \
		./bin/.site-packages/ \
		*.alfredworkflow

EXECUTABLES = $(PYTHON) plutil open rsync ./bin/workflow-build
K := $(foreach exec,$(EXECUTABLES),\
        $(if $(shell which $(exec)),some string,$(error "No $(exec) in PATH")))
