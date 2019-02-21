def select_templates(loc, spikes, bin_cat, n_exc, n_inh, min_dist=25, bound_x=None, min_amp=None, drift=False,
                     drift_dir_ang=[], preferred_dir=None, ang_tol=30, verbose=False):
    '''
    Parameters
    ----------
    loc
    spikes
    bin_cat
    n_exc
    n_inh
    min_dist
    bound_x
    min_amp
    drift
    drift_dir_ang
    preferred_dir
    ang_tol
    verbose
    Returns
    -------
    '''
    pos_sel = []
    idxs_sel = []
    exc_idxs = np.where(bin_cat == 'E')[0]
    inh_idxs = np.where(bin_cat == 'I')[0]

    if not min_amp:
        min_amp = 0

    if drift:
        if len(drift_dir_ang) == 0 or preferred_dir == None:
            raise Exception(
                'For drift selection provide drifting angles and preferred drift direction')

    for (idxs, num) in zip([exc_idxs, inh_idxs], [n_exc, n_inh]):
        n_sel = 0
        iter = 0
        while n_sel < num:
            # randomly draw a cell
            id_cell = idxs[np.random.permutation(len(idxs))[0]]
            dist = np.array([np.linalg.norm(loc[id_cell] - p)
                             for p in pos_sel])

            iter += 1

            if np.any(dist < min_dist):
                if verbose:
                    print('distance violation', dist, iter)
                pass
            else:
                amp = np.max(np.abs(spikes[id_cell]))
                if not drift:
                    if bound_x is None:
                        if amp > min_amp:
                            # save cell
                            pos_sel.append(loc[id_cell])
                            idxs_sel.append(id_cell)
                            n_sel += 1
                        else:
                            if verbose:
                                print('amp violation', amp, iter)
                    else:
                        if loc[id_cell][0] > bound_x[0] and loc[id_cell][0] < bound_x[1] and amp > min_amp:
                            # save cell
                            pos_sel.append(loc[id_cell])
                            idxs_sel.append(id_cell)
                            n_sel += 1
                        else:
                            if verbose:
                                print('boundary violation', loc[id_cell], iter)
                else:
                    # drift
                    if len(bound_x) == 0:
                        if amp > min_amp:
                            # save cell
                            if np.abs(drift_dir_ang[id_cell] - preferred_dir) < ang_tol:
                                pos_sel.append(loc[id_cell])
                                idxs_sel.append(id_cell)
                                n_sel += 1
                            else:
                                if verbose:
                                    print('drift violation',
                                          loc[id_cell], iter)
                        else:
                            if verbose:
                                print('amp violation', amp, iter)
                    else:
                        if loc[id_cell][0] > bound_x[0] and loc[id_cell][0] < bound_x[1] and amp > min_amp:
                            # save cell
                            if np.abs(drift_dir_ang[id_cell] - preferred_dir) < ang_tol:
                                pos_sel.append(loc[id_cell])
                                idxs_sel.append(id_cell)
                                n_sel += 1
                            else:
                                if verbose:
                                    print('drift violation',
                                          loc[id_cell], iter)
                        else:
                            if verbose:
                                print('boundary violation', loc[id_cell], iter)
    return idxs_sel
