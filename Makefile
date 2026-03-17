.PHONY: all data analyze figures clean

PYTHON ?= python3

all: data analyze figures

data:
	$(PYTHON) scripts/01_fetch_data.py

analyze: data
	$(PYTHON) scripts/02_analyze.py

figures: data
	$(PYTHON) scripts/03_make_figures.py

clean:
	rm -f data/gpi_tertiary_enrollment_raw.csv
	rm -f data/gpi_viz_data.json
	rm -f figs/*.png
