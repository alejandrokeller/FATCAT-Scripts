import numpy as np
import sys
from scipy.special import erf
from scipy.optimize import minimize,leastsq, curve_fit


def gauss(x):
    return np.exp( -0.5 * x**2)/np.sqrt( 2 * np.pi )

def my_triple_peak(x, A0, x0, s0, A1, x1, s1, A2, x2, s2):
    return A0 / s0 * gauss( ( x - x0 ) / s0 ) + A1 / s1 * gauss( ( x - x1 ) / s1 ) + A2 / s2 * gauss( ( x - x2 ) / s2 )

def my_4peak(x, A0, x0, s0, A1, x1, s1, A2, x2, s2, A3, x3, s3):
    return my_triple_peak(x, A0, x0, s0, A1, x1, s1, A2, x2, s2) + A3 / s3 * gauss( ( x - x3 ) / s3 )

def my_5peak(x, A0, x0, s0, A1, x1, s1, A2, x2, s2, A3, x3, s3, A4, x4, s4):
    return my_4peak(x, A0, x0, s0, A1, x1, s1, A2, x2, s2, A3, x3, s3) + A4 / s4 * gauss( ( x - x4 ) / s4 )

def my_fit(xdata, ydata, p0 = False, npeaks = 5):
                                
    nparameters = 3
    
    if npeaks == 3:
        if not p0:
            p0 = (10., 18., 3., 8., 28., 7., 6., 53., 8. )
            #      A0,  x0, s0, A1,  x1, s1, A2,  x2, s2
##        bounds=((0, 0, 0, 0, 20, 0, 0, 30, 0),
##                (np.inf, 20, np.inf, np.inf, 38, np.inf, np.inf, 60, 20))
        bounds=((0, 0, 0, 0, 20, 0, 0, 40, 0),
                (np.inf, 20, 5, np.inf, 40, 15, np.inf, 60, 20))
        peak_function = my_triple_peak
    elif npeaks == 4:
        if not p0:
            p0 = (100., 17., 6., 22., 23., 6., 80., 33., 8., 30., 51., 8. )
            #       A0,  x0, s0,   A1,  x1, s1, A2,   x2, s2,  A3,  x3, s3
##        bounds=((0, 0, 0, 0, 20, 0, 0, 27.5, 0, 0, 40, 0),
##                (np.inf, 20, 20, np.inf, 27.5, 20, np.inf, 40, 20, np.inf, 60, 20))
        bounds=((0, 15, 0, 0, 20, 0, 0, 31, 0, 0, 48, 0),
                (np.inf, 19, 20, np.inf, 24, 20, np.inf, 35, 20, np.inf, 52, 56))
        peak_function = my_4peak
    elif npeaks == 5:
        if not p0:
            p0 = (100., 17., 6., 22., 23., 10., 22., 23., 6., 80., 33., 8., 30., 51., 8. )
            #       A0,  x0, s0,  A1,  x1,  s1,  A2,  x2, s2,  A3,  x3, s3,  A4,  x4, s4
        bounds=((0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                (np.inf, 60, 20, np.inf, 60, 20, np.inf, 60, 20, np.inf, 60, 20, np.inf, 60, 20))
        peak_function = my_5peak

    fitResult, ier = curve_fit( peak_function, xdata, ydata, p0=p0, bounds = bounds )
        
    perr = np.sqrt(np.diag(ier))
    fit_coeff = []
    for n in range(int(len(fitResult)/nparameters)):
        coeffDict = {
            "A": fitResult[n*nparameters]/60,
            "xc" : fitResult[n*nparameters+1],
            "sigma" : fitResult[n*nparameters+2],
            "AStDevErr": perr[n*nparameters]/60,
            "xcStDevErr" : perr[n*nparameters+1],
            "sigmaStDevErr" : perr[n*nparameters+2],
        }
        fit_coeff.append(coeffDict)

    sorted_results = sorted(fit_coeff, key=lambda k: k['xc']) 
    
    bestFit = [peak_function(x, *fitResult ) for x in xdata ]

    # calculate r-squared
    residuals = ydata - bestFit
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((ydata-np.mean(ydata))**2)
    r_squared = 1 - (ss_res / ss_tot)

    return bestFit, sorted_results, r_squared
