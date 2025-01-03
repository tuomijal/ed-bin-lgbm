import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.metrics import roc_curve, auc

def get_history(series, history, name):
    """
    Take a series and generate history
    """
    vectors = []
    
    for h in range(history):
        v = series.shift(h)
        v.name = f'{name}_t-{h}'
        vectors.append(v)

    df = pd.concat(vectors, axis=1)
    df = df[df.columns[::-1]]
    
    return df

def make_true_matrix(y, h=1):
    """
    Make true matrix based on input vector.
    ----------
    Parameters
    y
        Target series
    h
        Horizons to generate 
    """
    trues = np.ones((len(y), h)) * np.nan

    for n, i in enumerate(y[:-h]):
        y_true = y[n:n+h]
        trues[n] = y_true

    columns = [f"t+{x+1}" for x in range(trues.shape[1])]
    
    result = pd.DataFrame(data=trues, 
                          index=y.index,
                          columns=columns)
    
    return result


colors = {
    'bed' : 'tab:blue',
    'med' : 'tab:red',
    'sur' : 'tab:orange',
    'cri' : 'tab:purple',
    'tuni:red' : '#CF2870',
    'tuni:green' : '#38B399',
    'tuni:yellow' : '#FEE349'
}


def bootstrap_auc(y_true, y_pred, n_boostrap=200):
    """
    """
    bootstrapped_scores = []
    
    for i in range(n_boostrap):
        indices = np.random.randint(0, len(y_pred), len(y_pred))
        
        fpr, tpr, thresholds = roc_curve(y_true[indices], y_pred[indices], pos_label=1)
        _auc = auc(fpr, tpr)
        bootstrapped_scores.append(_auc)
        
    bootstrapped_scores = np.array(bootstrapped_scores)
    sorted_scores = np.sort(bootstrapped_scores)
    
    confidence_lower = sorted_scores[int(0.05 * len(sorted_scores))]
    confidence_upper = sorted_scores[int(0.95 * len(sorted_scores))]
    
    return confidence_lower, confidence_upper