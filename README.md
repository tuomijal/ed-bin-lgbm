# Forecasting mortality associated emergency department crowding

Jalmari Tuominen, Anna Eidstö, Jari Ylä-Mattila, Teemu Koivistoinen, Niku Oksala, Juho Kanniainen, Ari Palomäki and Antti Roine


## Abstract 
Emergency department (ED) crowding is a global issue that been repeatedly associated with increased mortality. Predicting future crowding events is a prerequisite for preventative measures that aim to eliminate crowding along with it's detrimental effects. There is a growing body of ED forecasting literature but discrete predictions with binary crowded state as the target variable are widely neglected and forecasts are rarely stratified based on operational needs. Recently, we showed that in our facility, emergency department occupancy ratio over 90\% was associated with increased 10-day mortality. In this study, we document the performance of LightGBM model in predicting this mortality associated crowding using retrospective data from a large Nordic ED. We predict crowding of both medical and surgical subsections of the ED as well as total crowding among bedoccupying patients. We show that afternoon crowding can be predicted at 11 a.m. with AUC of 0.80 (95\% CI 0.76-0.84) among both bedoccupying and medical patients and at 8 a.m. with an AUC up to 0.78 (95\% CI 0.75-0.82).

## Usage

This repository uses GNU Make to manage the complete pipeline from raw data to manuscript PDF. To setup the correct environment first download this repository and create a virtual environment:

```
cd <DIR1>
git clone https://github.com/tuomijal/ed-bin-cat

python -m venv .env
source .env/bin/activate

brew install libomp
pip install -r requirements.txt
```


Update on 13.12.2024

You actually have to use python3.8 because otherwise calmap will break. If your python is not 3.8, get it e.g. with miniconda. 