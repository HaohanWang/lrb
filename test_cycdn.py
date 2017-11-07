from optparse import OptionParser

import numpy as np
from scipy import sparse
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
import cycdn


def main():
    usage = "%prog"
    parser = OptionParser(usage=usage)
    parser.add_option('--elim', action="store_true", dest="elimination", default=False,
                      help='Do heuristic variable elimination: default=%default')
    parser.add_option('--lower', dest='lower', default=-1000000.0,
                      help='Lower limit for weights: default=%default')
    parser.add_option('--upper', dest='upper', default=1000000.0,
                      help='Upper limit for weights: default=%default')
    parser.add_option('--tol', dest='tol', default=1e-5,
                      help='Tolerance for convergence (relative change in objective): default=%default')
    parser.add_option('--max_iter', dest='max_iter', default=200,
                      help='Maximum number of iterations: default=%default')
    parser.add_option('-n', dest='n', default=1000,
                      help='Number of instances: default=%default')
    parser.add_option('-p', dest='p', default=50,
                      help='Number of features: default=%default')
    parser.add_option('--sparsity_X', dest='sparsity_X', default=0.5,
                      help='Expected proportion of zero entries in X: default=%default')
    parser.add_option('--sparsity_beta', dest='sparsity_beta', default=0.5,
                      help='Expected proportion of zero entries in beta: default=%default')
    parser.add_option('--nonlinear', action="store_true", dest="nonlinear", default=False,
                      help='Generate nonlinear data for testing: default=%default')
    parser.add_option('--seed', dest='seed', default=None,
                      help='Random seed: default=%default')
    parser.add_option('--skl', action="store_true", dest="skl", default=False,
                      help='Use sklearn implementation: default=%default')
    parser.add_option('--both', action="store_true", dest="both", default=False,
                      help='Run both implementations and compare: default=%default')
    parser.add_option('-v', dest='verbose', default=2,
                      help='Verbosity level: default=%default')

    (options, args) = parser.parse_args()

    do_elimination = options.elimination
    lower = float(options.lower)
    upper = float(options.upper)
    tol = float(options.tol)
    max_iter = int(options.max_iter)
    n = int(options.n)
    p = int(options.p)
    sparsity_X = float(options.sparsity_X)
    sparsity_beta = float(options.sparsity_beta)
    nonlinear = options.nonlinear
    seed = options.seed
    use_skl = options.skl
    use_both = options.both
    verbose = int(options.verbose)

    if seed is not None:
        np.random.seed(int(seed))

    #X = np.array(np.random.randint(low=0, high=2, size=(n, p)), dtype=np.float64)
    X = np.array(np.random.binomial(p=1-sparsity_X, n=1, size=(n, p)), dtype=np.float64)
    beta_mask = np.array(np.random.binomial(p=1-sparsity_beta, n=1, size=p), dtype=np.float64)
    beta = np.array(np.random.randn(p), dtype=np.float64) * beta_mask
    if verbose > 0:
        print(beta)

    # make a non-linear problem to encourage line search
    if nonlinear:
        X2 = X**2
        beta2 = np.array(np.random.randn(p), dtype=np.float64) * np.random.randint(low=0, high=2, size=p)
        ps = expit(np.dot(X, beta) + np.dot(X2, beta2))
    else:
        ps = expit(np.dot(X, beta))
    y = np.random.binomial(p=ps, n=1, size=n)

    X = sparse.csc_matrix(X)

    if use_skl or use_both:
        model = LogisticRegression(C=1.0, penalty='l1', fit_intercept=False, solver='liblinear', tol=tol, max_iter=max_iter, verbose=verbose)
        model.fit(X, y)
        if verbose > 0:
            print(model.coef_)
        pred = model.predict(X)
        if verbose > 0:
            print(np.sum(np.abs(y - pred)) / float(n))

    if (not use_skl) or use_both:
        y2 = y.copy()
        y2[y == 0] = -1

        solver = cycdn.CDN(C=1.0, lower=lower, upper=upper, do_elimination=do_elimination)
        #solver.fit(X, y2, tol=1e-4, init_w=model.coef_[0], min_epochs=0, max_epochs=200, randomize=False, verbose=verbose)
        solver.fit(X, y2, tol=tol, max_epochs=max_iter, randomize=True, verbose=verbose)
        if verbose > 0:
            print(solver.get_w())

        pred_probs = solver.pred_probs(X)
        pred = np.argmax(pred_probs, axis=1)
        if verbose > 0:
            print(np.sum(np.abs(y - pred)) / float(n))

    if use_both:
        diff = np.abs(model.coef_[0] - solver.get_w())
        print("Maximum weight difference from skl:", np.max(diff))


if __name__ == '__main__':
    main()


