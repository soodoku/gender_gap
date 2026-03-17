.PHONY: all data lfpr analyze figures clean

PYTHON ?= python3

all: data lfpr analyze figures

data:
	$(PYTHON) scripts/01_fetch_data.py

lfpr:
	$(PYTHON) scripts/02_fetch_lfpr.py

analyze: data
	$(PYTHON) scripts/03_analyze.py

figures: data lfpr
	$(PYTHON) scripts/04_make_figures.py

clean:
	rm -f data/gpi_tertiary_enrollment_raw.csv
	rm -f data/gpi_viz_data.json
	rm -f figs/*.png
