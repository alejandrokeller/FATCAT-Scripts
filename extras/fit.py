import numpy as np
import sys
from scipy.special import erf
from scipy.optimize import minimize,leastsq, curve_fit


def gauss(x):
    return np.exp( -0.5 * x**2)/np.sqrt( 2 * np.pi )

def my_triple_peak(x, A0, x0, s0, A1, x1, s1, A2, x2, s2):
    return A0 / s0 * gauss( ( x - x0 ) / s0 ) + A1 / s1 * gauss( ( x - x1 ) / s1 ) + A2 / s2 * gauss( ( x - x2 ) / s2 )

def my_fit(xdata, ydata, p0 = (10., 18., 3., 8., 28., 7., 6., 53., 8. )):
    nparameters = 3
    
    fitResult, ier = curve_fit( my_triple_peak, xdata, ydata, p0=p0, 
                                bounds=((0, 0, 0, 0, 20, 0, 0, 37, 0),
                                        (np.inf, 20, np.inf, np.inf, 40, np.inf, np.inf, 60, 20)) )
    perr = np.sqrt(np.diag(ier))
    fit_coeff = []
    for n in range(nparameters):
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
        
#    print >>sys.stderr, "best fit: {}".format(sorted_results)
    
    bestFit = [my_triple_peak(x, *fitResult ) for x in xdata ]

    # calculate r-squared
    residuals = ydata - bestFit
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((ydata-np.mean(ydata))**2)
    r_squared = 1 - (ss_res / ss_tot)

    return bestFit, sorted_results, r_squared
