import numpy as np
import sys
from scipy.special import erf
from scipy.optimize import minimize,leastsq, curve_fit


def gauss(x):
    return np.exp( -0.5 * x**2)/np.sqrt( 2 * np.pi )

def _1gauss(x, A, xc, sigma):
    return A / sigma * gauss( ( x - xc ) / sigma )

def _2gauss(x, A0, x0, s0, A1, x1, s1):
    return _1gauss(x, A0, x0, s0) + A1 / s1 * gauss( ( x - x1 ) / s1 )

def _3gauss(x, A0, x0, s0, A1, x1, s1, A2, x2, s2):
    return _2gauss(x, A0, x0, s0, A1, x1, s1) + A2 / s2 * gauss( ( x - x2 ) / s2 )

def _4gauss(x, A0, x0, s0, A1, x1, s1, A2, x2, s2, A3, x3, s3):
    return _3gauss(x, A0, x0, s0, A1, x1, s1, A2, x2, s2) + A3 / s3 * gauss( ( x - x3 ) / s3 )

def _5gauss(x, A0, x0, s0, A1, x1, s1, A2, x2, s2, A3, x3, s3, A4, x4, s4):
    return _4gauss(x, A0, x0, s0, A1, x1, s1, A2, x2, s2, A3, x3, s3) + A4 / s4 * gauss( ( x - x4 ) / s4 )

def _6gauss(x, A0, x0, s0, A1, x1, s1, A2, x2, s2, A3, x3, s3, A4, x4, s4, A5, x5, s5):
    return _5gauss(x, A0, x0, s0, A1, x1, s1, A2, x2, s2, A3, x3, s3, A4, x4, s4) + A5 / s5 * gauss( ( x - x5 ) / s5 )

def my_fit(xdata, ydata, p0 = False, npeaks = 5):
                                
    nparameters = 3

    if npeaks == 1:
        if not p0:
            p0 = (10., 18., 3.)
            #      A0,  x0, s0
        bounds=((0, 0, 0),
                (np.inf, np.inf, np.inf))
        peak_function = _1gauss
    elif npeaks == 2:
        if not p0:
            p0 = (10., 18., 3., 8., 28., 7.)
            #      A0,  x0, s0, A1,  x1, s1
        bounds=((0, 0, 0, 0, 0, 0),
                (np.inf, np.inf, 20, np.inf, np.inf, 20))
        peak_function = _2gauss
    elif npeaks == 3:
        if not p0:
            p0 = (10., 15., 3., 8., 33., 7., 6., 53., 8. )
            #      A0,  x0, s0, A1,  x1, s1, A2,  x2, s2
##        bounds=((0, 0, 0, 0, 20, 0, 0, 30, 0),
##                (np.inf, 20, np.inf, np.inf, 38, np.inf, np.inf, 60, 20))
## Before Aerotox--- used for Schimmelstrasse in ZH
        bounds=(     (0,  0, 1.5,      0, 28,  1.5,      0, 40,  1.5),
                (np.inf, 20, 5, np.inf, 40, 10, np.inf, 60, 10))
## Very constrained peaks
##        bounds=(     (0,  0, 1.5,    0, 35,  1.5,    0, 55,  1.5),
##                (np.inf, 30, 5, np.inf, 47, 10, np.inf, 65, 10))
        peak_function = _3gauss
    elif npeaks == 4:
        if not p0:
            p0 = ( 100., 15., 3.,   22., 19., 5.,   80., 33., 8.,  30., 51., 8. )
            #       A0,  x0, s0,     A1,  x1, s1,    A2,  x2, s2,   A3,  x3, s3
##        bounds=((0, 0, 0, 0, 20, 0, 0, 27.5, 0, 0, 40, 0),
##                (np.inf, 20, 20, np.inf, 27.5, 20, np.inf, 40, 20, np.inf, 60, 20))
        bounds=((     0,  0, 1.5,      0, 17, 1.5,      0, 28, 1.5,     0, 40, 1.5),
                (np.inf, 19,   6, np.inf, 25,   8, np.inf, 37, 20, np.inf, 60, 10))
        peak_function = _4gauss
    elif npeaks == 5:
        if not p0:
            p0 = ( 100., 15., 3.,  22., 22., 5., 22., 35., 5.,  80., 30., 5.,   30., 51., 5. )
            #        A0, x0, s0,   A1,  x1,  s1,  A2, x2, s2,   A3,  x3, s3,     A4, x4, s4
        bounds=((     0,  0, 1.5,      0, 19, 1.5,      0, 28, 1.5,      0, 28, 1.5,      0, 48, 1.5),
                (np.inf, 19,   8, np.inf, 25,   8, np.inf, 35,   8, np.inf, 37,  10, np.inf, 60, 10))
        peak_function = _5gauss
    elif npeaks == 6:
        if not p0:
            p0 = (100., 15., 3., 22., 22., 5., 10., 27., 5., 22., 34., 6., 80., 46., 8., 30., 54., 8. )
            #       A0,  x0, s0,  A1,  x1, s1,  A2,  x2, s2,  A3,  x3, s3,  A4,  x4, s4,  A5,  x5, s5
        bounds=((     0,  0, 1.5,      0, 17, 1.5,      0, 22, 1.5,      0, 28, 1.5,      0, 37, 1.5,      0, 46, 1.5),
                (np.inf, 19,   6, np.inf, 23,   7, np.inf, 32,   8, np.inf, 40,  10, np.inf, 50,  10, np.inf, 60, 10))
        peak_function = _6gauss
    else:
        print >>sys.stderr, "number of peaks not defined in fitting function: {}".format(npeaks)

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
