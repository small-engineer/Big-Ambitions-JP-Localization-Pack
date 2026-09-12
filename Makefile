PYTHON ?= python3
WORKSHOP_DIR ?= /Users/home/Library/Application Support/Steam/steamapps/workshop/content/1331550
MANAGED_DIR ?= /Users/home/Library/Application Support/Steam/steamapps/common/Big Ambitions/Big Ambitions.app/Contents/Resources/Data/Managed

PROJECT := src/BigAmbitions.JpLocalizationPack/BigAmbitions.JpLocalizationPack.csproj
DLL := src/BigAmbitions.JpLocalizationPack/bin/Release/netstandard2.1/BigAmbitions.JpLocalizationPack.dll
PACK_DIR := dist/BigAmbitionsJapanesePack

.PHONY: all sync locales dll package check

all: package

sync:
	$(PYTHON) -B sync_workshop.py --workshop-dir "$(WORKSHOP_DIR)"

locales: sync
	$(PYTHON) -B build.py

dll:
	dotnet build "$(PROJECT)" -c Release "-p:BigAmbitionsManagedDir=$(MANAGED_DIR)"

package: locales dll
	mkdir -p "$(PACK_DIR)/Locales"
	cp "$(DLL)" "$(PACK_DIR)/BigAmbitions.JpLocalizationPack.dll"
	cp Locales/ja.json "$(PACK_DIR)/Locales/ja.json"
	cp thumbnail.png "$(PACK_DIR)/thumbnail.png"

check:
	$(PYTHON) -B sync_workshop.py --workshop-dir "$(WORKSHOP_DIR)" --check
	$(PYTHON) -B build.py --check
	dotnet build "$(PROJECT)" -c Release --no-restore "-p:BigAmbitionsManagedDir=$(MANAGED_DIR)"
	test -f thumbnail.png
	test "$$(wc -c < thumbnail.png)" -le 1000000
