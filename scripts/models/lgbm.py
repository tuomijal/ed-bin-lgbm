import optuna
from optuna.integration import LightGBMPruningCallback

from darts.models import LightGBMClassifier
from darts.metrics import mae, f1, logloss
from lightgbm import early_stopping
from optuna.samplers import TPESampler

import numpy as np
import logging

def get_categorical_future_covariates():
    """
    """
    gfc = ['Calendar:Month', 
           'Calendar:Weekday', 
           'Calendar:Holiday'
           ]
    return gfc

def build_fit(
    y_train, 
    y_val, 
    pc_train, 
    fc_train, 
    pc_val, 
    fc_val,
    params,
    args,
    **kwargs
    ):
    """
    """

    esc = early_stopping(args.patience, verbose=True)
    callbacks = []

    if 'LighGBMPruningCallback' in params.keys():
        pruner = params['LighGBMPruningCallback']
        callbacks.append(pruner)

    model = LightGBMClassifier(
        lags=params['lags'],
        lags_past_covariates=params['lags'] if pc_train is not None else None,
        lags_future_covariates=(params['lags'], 1) if fc_train is not None else None,
        num_leaves=params['num_leaves'], 
        learning_rate=params['learning_rate'], 
        n_estimators=params['n_estimators'],
        min_child_samples=params['min_child_samples'], 
        subsample=params['subsample'],
        random_state=args.randomstate,
        categorical_future_covariates=get_categorical_future_covariates() if fc_train is not None else None,
        output_chunk_length=args.output_chunk_length,
        scale_pos_weight=args.scale_pos_weight
    )
    
    
    # train the model
    model.fit(
        series=y_train,
        future_covariates=fc_train if model.supports_future_covariates else None, 
        past_covariates=pc_train if model.supports_past_covariates else None,
        val_series=y_val,
        val_future_covariates=fc_val if model.supports_future_covariates else None,
        val_past_covariates=pc_val if model.supports_past_covariates else None,
        callbacks=callbacks
    )

    return model


class Objective(object):
    """
    """
    def __init__(self, y_train, y_val, pc_train, fc_train, pc_val, fc_val, args):
        self.y_train = y_train
        self.y_val = y_val
        self.pc_train = pc_train
        self.fc_train = fc_train
        self.pc_val = pc_val
        self.fc_val = fc_val
        self.args = args

    def __call__(self, trial):

        params = {}

        params['lags'] = trial.suggest_categorical('lags', [7, 14, 21, 28])
        params['num_leaves'] = trial.suggest_int('num_leaves', 15, 186)
        params['learning_rate'] = trial.suggest_categorical("learning_rate", [1e-5, 1e-4, 1e-3, 1e-2, 1e-1])
        params['n_estimators'] = trial.suggest_int('n_estimators', 50, 100)
        params['min_child_samples'] = trial.suggest_int('min_child_samples', 10, 120)
        params['subsample'] = trial.suggest_float('subsample', 0.1, 1.00)

        # build and train the model with these hyper-parameters:
        model = build_fit(
            y_train=self.y_train,
            y_val=self.y_val,
            pc_train=self.pc_train,
            pc_val=self.pc_val,
            fc_train=self.fc_train,
            fc_val=self.fc_val,
            params=params,
            args=self.args
        )

        pc = self.pc_train.append(self.pc_val) if self.pc_train is not None else None
        fc = self.fc_train.append(self.fc_val) if self.fc_train is not None else None

        error = model.backtest(
                series=self.y_train.append(self.y_val),
                future_covariates=fc if model.supports_future_covariates else None,
                past_covariates=pc if model.supports_past_covariates else None,
                start=self.y_val.start_time(),
                stride=1,
                metric=logloss,
                forecast_horizon=1,
                retrain=1
            )

        return error


def get_model(y_train, 
              y_val, 
              pc_train, 
              fc_train, 
              pc_val, 
              fc_val,
              args):
    """
    """

    default_params = {
        'lags' : 28,
        'num_leaves' : 31,
        'learning_rate' : 0.1,
        'n_estimators' : 100,
        'subsample_for_bin' : 200_000,
        'min_child_samples' : 20,
        'subsample' : 1.0
    }

    if args.hpo_indicator:
        logging.info('Starting hyperparameter optimisation as requested')
        logging.info(f'HPO method: OPTUNA with timeout: {args.timeout}')
        
        objective = Objective(y_train, y_val, pc_train, fc_train, pc_val, fc_val, args)
        study = optuna.create_study(direction="minimize", sampler=TPESampler(seed=args.randomstate))
        study.enqueue_trial(default_params)
        study.optimize(
            objective, 
            timeout=args.timeout, 
            n_trials=args.ntrials
            )

        print(f"Best value: {study.best_value}, Best params: {study.best_trial.params}")
        params = study.best_trial.params
    else:
        logging.info("Skipping HPO per request or as unnecessary")
        params = default_params
        study = None
    
    logging.info("Fitting the model for the first time")
    model = build_fit(
            y_train=y_train,
            y_val=y_val,
            pc_train=pc_train,
            pc_val=pc_val,
            fc_train=fc_train,
            fc_val=fc_val,
            params=params,
            args=args
        )
    
    return model, study

