.PHONY: all preddata

#################################################################################
# GLOBALS                                                                       #
#################################################################################

SHELL = /bin/zsh

plotdir = output/plots

TEXFILES = report/sections/abstract.tex\
	report/sections/conclusions.tex\
	report/sections/discussion.tex\
	report/sections/introduction.tex\
	report/sections/materials_and_methods.tex\
	report/sections/results.tex\
	report/sections/appendix.tex\
	report/sections/declarations.tex\
	report/manuscript.tex\

TABLES = output/tables/metrics.tex\
	output/tables/metrics_all.tex\
	output/tables/variables.tex

PLOTSPARAM = $(plotdir)/calmap-bed.png\
	$(plotdir)/calmap-sur.png\
	$(plotdir)/calmap-med.png\
	$(plotdir)/heatmap-bed.png\
	$(plotdir)/heatmap-med.png\
	$(plotdir)/heatmap-sur.png\
	$(plotdir)/aucorigin-bed.png\
	$(plotdir)/aucorigin-med.png\
	$(plotdir)/aucorigin-sur.png\
	
	
PLOTS2 = $(plotdir)/auc.png\
	$(plotdir)/prcurve.png\
	$(plotdir)/shap.png\
	$(plotdir)/lime.png\
	$(plotdir)/edor-example.png\
	$(plotdir)/bars.png\
	$(plotdir)/variables.png\

PARAMNTB = notebooks/plot_calmap.ipynb\
	notebooks/plot_heatmap.ipynb\
	notebooks/plot_shap.ipynb

PLOTERRORMAP = $(plotdir)/errormap-med-lgbm-11-0-0.png\
	$(plotdir)/errormap-bed-lgbm-11-0-0.png\
	$(plotdir)/errormap-sur-lgbm-11-0-0.png\
	

probdir := data/processed/matrices/prob
pointdir := data/processed/matrices/point

	
# Define the components
SECTIONS = med bed sur
MODELS = lgbm xgbo catb
TIMES = 8 9 10 11 12

# Create the combinations using nested foreach
POINTS = $(foreach sect,$(SECTIONS),\
	$(foreach model,$(MODELS),\
		$(foreach time,$(TIMES),\
			$(pointdir)/$(sect)-$(model)-$(time)-0-0.csv\
		)\
	)\
)

# Create the combinations using nested foreach
PROBS = $(foreach sect,$(SECTIONS),\
	$(foreach model,$(MODELS),\
		$(foreach time,$(TIMES),\
			$(probdir)/$(sect)-$(model)-$(time)-0-0.csv\
		)\
	)\
)

truedir := data/processed/true_matrices

TRUE = $(truedir)/bed.csv\
	$(truedir)/sur.csv\
	$(truedir)/med.csv\


MELTED = data/interim/melted.csv

MODEL = data/model/data-8.csv\
	data/model/data-9.csv\
	data/model/data-10.csv\
	data/model/data-11.csv\
	data/model/data-12.csv\
	data/model/data-13.csv\

INTERIM = data/interim/data.csv\

PREPROCESSED = data/preprocessed/targets.csv\
	data/preprocessed/calendar.csv\
	data/preprocessed/beds.csv\
	data/preprocessed/weather.csv\

PLOTS = $(PLOTERRORMAP) $(PLOTSPARAM) $(PLOTS2)

#################################################################################
# FUNCTIONS                                                                     #
#################################################################################

# $(call get_word, position_in_list, list) 
# Get nth element from {w1}-{w2}-{w3}-..-{wn}
define get_word
$(word $(1),$(subst -, ,$(basename $(notdir $(2)))))
endef

#################################################################################
# COMMANDS                                                                      #
#################################################################################

all: output/manuscript.pdf

preds: $(POINTS)

output/manuscript.pdf: $(PLOTS) $(TABLES) $(TEXFILES) report/manuscript.tex report/references.bib
	cd report\
	&& pdflatex manuscript\
	&& bibtex manuscript\
	&& pdflatex manuscript\
	&& pdflatex manuscript\
	&& cp manuscript.pdf ../output/manuscript.pdf\
	&& cp manuscript.pdf ~/Desktop/ed-bin-cat.pdf\
	&& open manuscript.pdf\
	

$(TABLES): output/tables/%.tex : notebooks/tab_%.ipynb $(TRUE) 
	cd notebooks\
	&& papermill $(notdir $<) /dev/null

$(PLOTS2): output/plots/%.png : notebooks/plot_%.ipynb $(TRUE) 
	cd notebooks\
	&& papermill $(notdir $<) /dev/null

$(PLOTERRORMAP): $(TRUE) notebooks/plot_errormap.ipynb 
	cd notebooks\
	&& papermill plot_$(call get_word,1,$@).ipynb /dev/null\
	 -p TARGET $(call get_word,2,$@)\
	 -p MODEL $(call get_word,3,$@)\
	 -p ORIGIN $(call get_word,4,$@)\
	 -p FS $(call get_word,5,$@)\
	 -p HPO $(call get_word,6,$@)

$(PLOTSPARAM): data/interim/data.csv $(PARAMNTB)
	cd notebooks\
	&& papermill plot_$(call get_word,1,$@).ipynb /dev/null -p TARGET $(call get_word,2,$@)

$(POINTS): notebooks/make_points.ipynb $(TRUE) $(PROBS)
	cd notebooks\
	&& papermill make_points.ipynb /dev/null

$(PROBS): scripts/test.py $(MELTED)
	cd scripts\
	&& python test.py $(call get_word,1,$@) $(call get_word,2,$@) $(call get_word,3,$@) $(call get_word,4,$@) $(call get_word,5,$@) $(call get_word,6,$@);\

$(TRUE): notebooks/make_true_matrices.ipynb data/preprocessed/targets.csv
	cd notebooks\
	&& papermill make_true_matrices.ipynb /dev/null -p TARGET $(call get_word,1,$@)

$(MELTED): $(MODEL)
	cd notebooks\
	&& papermill make_melted.ipynb /dev/null

$(MODEL): $(INTERIM) notebooks/make_model_data.ipynb
	cd notebooks\
	&& papermill make_model_data.ipynb -p ORIGIN $(call get_word,2,$@) /dev/null

$(INTERIM): $(PREPROCESSED) notebooks/make_interim_data.ipynb
	cd notebooks\
	&& papermill make_interim_data.ipynb /dev/null

$(PREPROCESSED): data/preprocessed/%.csv : notebooks/make_%.ipynb
	cd notebooks\
	&& papermill $(notdir $<) /dev/null

data/raw/data.csv: notebooks/make_raw_data.ipynb
	cd notebooks\
	&& papermill make_raw_data.ipynb /dev/null

#################################################################################
# Helper Commands																#
#################################################################################

clean:
	rm -rf data/processed/*
	rm -r output/*

clear_report:
	rm report/manuscript.bbl
	rm report/manuscript.blg
	rm report/manuscript.log
	rm report/manuscript.out
	rm report/manuscript.aux

clear_notebooks:
	jupyter nbconvert notebooks/*.ipynb --clear-output --inplace

clear_results:
	rm -rf data/processed/matrices
	rm -rf data/processed/models
	rm -rf data/processed/studies
	rm -rf darts_logs
	rm logs/slurm/*
	rm logs/logger/*