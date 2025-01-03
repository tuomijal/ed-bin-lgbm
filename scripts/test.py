#!/usr/bin/env python
# coding: utf-8

import pandas as pd
from pyprojroot import here
import logging
from tqdm import tqdm
import numpy as np
import argparse
import os
import joblib

from xgboost import XGBClassifier
from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier

def main(args):
    """
    Main entry point for the backtesting logic
    """
    # SETTINGS
    args.timeout = args.timeout if args.timeout else int(os.environ.get('TIMEOUT', 86400))
    args.patience = args.patience if args.patience else int(os.environ.get('PATIENCE', 10))
    args.randomstate = int(args.randomstate) if args.randomstate is not None else 68123
    args.firstsplit = args.valstart if args.valstart else os.environ.get('FIRSTSPLIT', '20190101')
    args.secondsplit = args.teststart if args.teststart else os.environ.get('SECONDSPLIT', '20190228')
    args.firstsplit = pd.Timestamp(args.firstsplit)
    args.secondsplit = pd.Timestamp(args.secondsplit)
    args.ntrials = args.ntrials if args.ntrials else int(os.environ.get('NTRIALS', 30))
    args.origin = int(args.origin)
    
    ## Preprocess
    logging.basicConfig(
        format='%(asctime)s - %(message)s', 
        level=logging.INFO,
        filename=here() / f"logs/logger/{args.target}-{args.model}-{args.origin}-{args.hpo_indicator}-{args.fs_indicator}.log",
        filemode='w'
        )

    logging.info('Starting test.')
    logging.info(f'MODEL: {args.model} TARGET: {args.target} ORIGIN: {args.origin} HPO: {args.hpo_indicator} FS: {args.fs_indicator} TIMEOUT: {args.timeout} RANDOMSTATE: {args.randomstate} NTRIALS: {args.ntrials}')

    data = pd.read_csv(here() / f'data/interim/melted.csv', index_col='Datetime', parse_dates=True)
    
    ui = data.index.unique()
    test_indices = ui[ui >= pd.Timestamp('2019-01-01')]

    if args.model=='guess':
        y_probs = pd.Series(index=test_indices, data=np.random.rand(test_indices.shape[0]))
        y_probs.index.name = 'Datetime'
        y_probs.to_csv(here() / f'data/processed/matrices/prob/{args.target}-{args.model}-{args.origin}-{args.hpo_indicator}-{args.fs_indicator}.csv')
        return
    elif args.model=='xgbo':
        model = XGBClassifier(objective='binary:logistic', random_state=args.randomstate)
    elif args.model=='catb':
        model = CatBoostClassifier(random_state=args.randomstate)
    elif args.model=='lgbm':
        model = LGBMClassifier(class_weight='balanced', verbose=-1, random_state=args.randomstate)
    else:
        raise ValueError(f'Model {args.model} not supported')

    # if args.fs_indicator==1:
    #     logging.info('Starting feature selection')
    #     sfs = SequentialFeatureSelector(model, tol=0)
    #     sfs.fit(X_train, y_train)
    #     mask = sfs.get_support()
    #     X = X.loc[:,mask]
    #     logging.info('Stopping feature selection')

    # if args.hpo_indicator==1:
    #     logging.info('Starting HPO')
    #     params = get_params(y_train, y_val, X_train, X_val)
    #     logging.info('Stopping HPO')
    # else:
    #     params = defaultparams
    
    logging.info('Starting backtesting on the test set')

    results = list()

    for i in tqdm(test_indices):
        train_data = data[data.index < i]
        test_data = data[data.index == i]

        X_train = train_data.drop(columns='Crowding')
        y_train = train_data['Crowding']

        X_test = test_data.drop(columns='Crowding')

        model.fit(X_train, y_train)
        y_prob = model.predict_proba(X_test)

        X_test['y_pred'] = y_prob[:,1]
        results.append(X_test[['Origin', 'Subgroup', 'y_pred']])

    df = pd.concat(results)
    
    conversion = {0: 'bed',
                  1: 'med',
                  2: 'sur',
                  3: 'cri'}
    
    df.Subgroup = df.Subgroup.replace(conversion)
    
    for s in df.Subgroup.unique():
        for o in df.Origin.unique():
            d = df[(df.Subgroup==s) & (df.Origin==o)]

            folder = here() / 'data/processed/matrices/prob/'
            if not os.path.exists(folder):
                os.makedirs(folder)
            d['y_pred'].to_csv(folder / f'{s}-{args.model}-{o}-0-0.csv')
    
    # Persist model
    folder = here() / 'data/processed/models/'
    if not os.path.exists(folder):
        os.makedirs(folder)

    joblib.dump(model, str(folder / f'{args.model}-{args.hpo_indicator}-{args.fs_indicator}.pkl'))

    logging.info('Results persisted')


def parse_arguments():
    """
    Argument parsing
    """
    parser = argparse.ArgumentParser(description='CLI interface to run a specific test.')
    # Define the positional arguments
    parser.add_argument('target', 
                        choices=['bed', 'med', 'sur', 'cri'], help='Target to be tested.', 
                        metavar='target')
    parser.add_argument('model', 
                        choices=['lgbm', 'guess', 'xgbo', 'catb'], 
                        help='Model to be tested. Choose from: deepar, lgbm, nbeats, tft, sn, arimax, hwmm, hwdm, hwam.',
                        metavar='model')
    parser.add_argument('origin', 
                        help='Origin for predictions. Must be a number',
                        metavar='origin')
    parser.add_argument('hpo_indicator', 
                        choices=[0, 1, 2], 
                        type=int, 
                        help='Indicator to either perform HPO iteratively (2), once (1) or skip it (0).',
                        metavar='hpo_indicator')
    parser.add_argument('fs_indicator', 
                        choices=[0, 1], 
                        type=int, 
                        help='Indicator to either perform FS (1) or skip it (0).',
                        metavar='fs_indicator')
    parser.add_argument('-t', '--timeout', 
                        help="Timeout for hyperparameter optimisation in seconds", 
                        type=int,
                        metavar='')
    parser.add_argument('-p', '--patience', 
                        help="Early stopping callback patience value", 
                        type=int,
                        metavar='')
    parser.add_argument('-e', '--epochs', 
                        help="Max number of epochs", 
                        type=int,
                        metavar='')
    parser.add_argument('-n', '--name', 
                        help="Additional identifier for persistence",
                        metavar='')
    parser.add_argument('-V', '--valstart', 
                        help="Validation start date",
                        metavar='')
    parser.add_argument('-T', '--teststart', 
                        help="Test start date",
                        metavar='')
    parser.add_argument('-S', '--headstart', 
                        help="Data start date",
                        metavar='')
    parser.add_argument('-E', '--tailstop', 
                        help="Data end date",
                        metavar='')
    parser.add_argument('-r', '--randomstate', 
                        help="Random state for reproducibility", 
                        type=int,
                        metavar='')
    parser.add_argument('-N', '--ntrials', 
                        help="Number of HPO trials to perform", 
                        type=int,
                        metavar='')

    args = parser.parse_args()
    return args


if __name__=='__main__':
    args = parse_arguments()
    main(args)