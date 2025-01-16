# Forecasting Mortality Associated Emergency Department Crowding with LightGBM and Time Series Data

This repository contains code, data and raw text for the following article:

Authors:

**Jalmari Nevanlinna (1), Anna Eidstø (1,2), Jari Ylä-Mattila (1,2), Teemu Koivistoinen (4), Niku Oksala (1,3), Juho Kanniainen (5), Ari Palomäki (1,4) and Antti Roine (1)**

1) *Faculty of Medicine and Health Technology, Tampere University*
2) *Emergency Department, Tampere University Hospital, Tampere, Finland*
3) *Centre for Vascular Surgery and Interventional Radiology, Tampere University Hospital*
4) *Kanta-Häme Central Hospital, Hämeenlinna, Finland*
5) *Faculty of Information Technology and Communication Sciences, Tampere University, Tampere, Finland*


## Abstract 
Emergency department (ED) crowding is a global public health issue that has been repeatedly associated with increased mortality. Predicting future service demand would enable preventative measures aiming to eliminate crowding along with it's detrimental effects. Recent findings in our ED indicate that occupancy ratios exceeding 90\% are associated with increased 10-day mortality. In this paper, we aim to predict these crisis periods using retrospective time series data such as weather, availability of hospital beds, calendar variables and occupancy statistics from a large Nordic ED with a LightGBM model. We predict mortality associated crowding for the whole ED and individually for it's different operational sections. We demonstrate that afternoon crowding can be predicted at 11 a.m. with an AUC of 0.82 (95% CI 0.78-0.86) and at 8 a.m. with an AUC up to 0.78 (95% CI 0.74-0.82). Consequently we show that forecasting mortality-associated crowding using time series data is feasible.


## Usage

This repository uses GNU Make to manage the complete pipeline from raw data to manuscript PDF. To reproduce the results, follow these instructions:

```
git clone https://github.com/tuomijal/ed-bin-lgbm
cd ed-bin-lgbm

python -m venv .env
source .env/bin/activate

brew install libomp
pip install -r requirements.txt

make preds
make
```