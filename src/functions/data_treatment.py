from astropy.io import fits
import numpy as np
from scipy.ndimage import uniform_filter1d
from fastdtw import fastdtw
from datetime import datetime

# ======== Funções de pré-processamento ========

def load_fits_data(fits_path: str, idx: int = 4) -> tuple[np.ndarray, fits.fitsrec.FITS_rec, str]:
    """
    Read and load the fits data.

    Parameters
    ----------
    fits_path : str
        Path for the file to be opened.

    idx : int, default=4
        The position of the curve to be loaded in the fits file. Possible values are::

            4 -> "TBL_45"
            5 -> "TBR_45"
            6 -> "TBL_90"
            7 -> "TBR_90"

    Returns
    -------
    np.ndarray
        Values of the selected type of curve.

    fits.fitsrec.FITS_rec
        The fits table of that file.

    str
        The date of the event (YYYY-MM-DD format)
    """
    with fits.open(fits_path) as hdul:        
        # Ler dados da tabela binária
        tabela = hdul[1].data

        col_y = tabela.names[idx]

        col_data = tabela.names[0]

        data = tabela[col_y]
        full_table = tabela
        day = tabela[col_data][0]

        return data, full_table, day

def clip_outliers_iqr(arr: np.ndarray, factor: float = 1.5):
    """
    Clip outliers in a 1D array using the interquartile range (IQR) method.

    Parameters
    ----------
    arr : np.ndarray
        Input light curve data as a 1D array.

    factor : float, default=1.5
        Multiplier for the interquartile range (IQR) to define outlier thresholds.
        Values lower than Q1 - factor*IQR or higher than Q3 + factor*IQR are clipped to the threshold.
        
    Returns
    -------
    np.ndarray
        The input array with values clipped to the range
        [Q1 - factor*IQR, Q3 + factor*IQR].
    """
    q1, q3 = np.percentile(arr, [25, 75])
    iqr = q3 - q1
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr
    return np.clip(arr, lower, upper)

def z_score_norm(arr: np.ndarray) -> np.ndarray:
    """
    Apply z-score normalization to an array.

    Parameters
    ----------
    arr : np.ndarray
        Input light curve data as a 1D array.

    Returns
    -------
    np.ndarray
        Array of the same shape as input, with values normalized by z-score.
    """
    mean = np.mean(arr)
    std = np.std(arr)
    return (arr - mean) / std if std > 0 else arr - mean

def preprocess_curve(
    arr: np.ndarray,
    smooth_window: int = 125,
    n_apply_smooth: int = 2
) -> np.ndarray:
    """
    Preprocess a Sun light curve by clipping outliers, normalizing, and smoothing.

    The preprocessing steps are applied in the following order:
    1. Outlier clipping (`clip_outliers_iqr`).
    2. Z-score normalization (`z_score_norm`).
    3. Smoothing (`apply_smooth`).

    Parameters
    ----------
    arr : np.ndarray
        Input light curve data as a 1D array.

    smooth_window : int, default=125
        Number of neighbours to apply the smoothing.

    n_apply_smooth : int, default=2
        Number of iterations to apply the smoothing with `smooth_window` neighbours.

    Returns
    -------
    np.ndarray
        Preprocessed light curve, same shape as input.
    """
    arr = clip_outliers_iqr(arr, factor=1.5)
    arr = z_score_norm(arr)
    arr = apply_smooth(arr, smooth_window, n_apply_smooth)
    return arr

def apply_smooth(arr: np.ndarray, smooth_window: int = 125, n_apply_smooth: int = 2) -> np.ndarray:
    """
    Smooth a 1D array using a uniform moving average filter.

    The smoothing is applied `n_apply_smooth` times consecutively, using
    a uniform filter with a window of size `smooth_window`.

    Parameters
    ----------
    arr : np.ndarray
        Input light curve data as a 1D array.

    smooth_window : int, default=125
        Number of neighbours to apply the smoothing.

    n_apply_smooth : int, default=2
        Number of iterations to apply the smoothing with `smooth_window` neighbours.

    Returns
    -------
    np.ndarray
        Smoothed array of the same shape as input.
    """
    for _ in range(n_apply_smooth):
        arr = uniform_filter1d(arr, size=smooth_window, mode="nearest")
    return arr


def interpolate_curve(arr: np.ndarray, target_len: int) -> np.ndarray:
    """
    Interpolate a 1D array to a target length using linear interpolation.

    Parameters
    ----------
    arr : np.ndarray
        Input light curve data as a 1D array.

    target_len : int
        Desired length of the output array.

    Returns
    -------
    np.ndarray
        Interpolated array of length `target_len`.
    """
    x_old = np.linspace(0, 1, num=len(arr))
    x_new = np.linspace(0, 1, num=target_len)
    return np.interp(x_new, x_old, arr)


# ======== Função FastDTW ========

def calcular_fastdtw(idx: int, curva_interp: np.ndarray, target_interp: np.ndarray) -> tuple[int, float]:
    """
    Calculate the FastDTW distance between an interpolated curve and a target curve.

    Parameters
    ----------
    idx : int
        Index of the curve being compared (used for tracking/debugging purposes).

    curva_interp : np.ndarray
        Interpolated curve to compare.

    target_interp : np.ndarray
        Interpolated target curve to compare against.

    Returns
    -------
    tuple[int, float]
        A tuple containing:
        - The index of the curve (`idx`).
        - The FastDTW distance between `curva_interp` and `target_interp`.
          Returns `float('inf')` if an exception occurs during computation.
    """
    try:
        curva_1d = np.asarray(curva_interp, dtype=float).ravel().tolist()
        target_1d = np.asarray(target_interp, dtype=float).ravel().tolist()

        # Debug
        # print(f"[DEBUG] Curva {idx}")
        # print(f"  curva_1d.shape = {len(curva_1d)}")
        # print(f"  target_1d.shape = {len(target_1d)}")
        # print(f"  curva_1d[:5] = {curva_1d[:5]}")
        # print(f"  target_1d[:5] = {target_1d[:5]}")

        dist, _ = fastdtw(target_1d, curva_1d)
        return idx, dist
    except Exception as e:
        print(f"Erro na curva {idx} (fastdtw): {e}")
        return idx, float('inf')
    

# ======== Funções para os intervalos ========


def merge_intervals(intervals: list[tuple[float, float]], gap: int = 5) -> list[tuple[float, float]]:
    """
    Merge overlapping or close intervals in a list.

    Parameters
    ----------
    intervals : list of tuple[float, float]
        List of intervals, each represented as a tuple (start, end).

    gap : int, default=5
        Maximum allowed gap between intervals to merge them.

    Returns
    -------
    list of tuple[float, float]
        List of merged intervals, sorted by start time.
    """
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda x: x[0])
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end + gap:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def find_common_intervals_precise(intervals_list: list[list[tuple[float, float]]], min_curves: int) -> list[tuple[float, float]]:
    """
    Find intervals where at least a minimum number of curves overlap.

    Parameters
    ----------
    intervals_list : list of list of tuple[float, float]
        Each element corresponds to a curve and contains a list of intervals
        (start, end) representing active regions for that curve.
        
    min_curves : int
        Minimum number of curves that must overlap for an interval to be included.

    Returns
    -------
    list of tuple[float, float]
        List of intervals where at least `min_curves` curves overlap.
    """
    # Gerar eventos (posição, +1 ou -1)
    events = []
    for curve_idx, intervals in enumerate(intervals_list):
        for start, end in intervals:
            events.append((start, +1))
            events.append((end, -1))

    # Ordenar eventos por posição
    events.sort(key=lambda x: (x[0], -x[1]))  # Abrir (+1) antes de fechar (-1) no mesmo ponto

    intervals_common = []
    active_count = 0
    current_start = None

    for pos, change in events:
        previous_active = active_count
        active_count += change
        
        # Entrando em região onde temos >= min_curves
        if previous_active < min_curves and active_count >= min_curves:
            current_start = pos
        # Saindo da região com >= min_curves
        elif previous_active >= min_curves and active_count < min_curves:
            current_end = pos
            intervals_common.append((current_start, current_end))
            current_start = None

    return intervals_common


def generate_datetime_list(target_full_table: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate a list of datetime objects and corresponding datetime strings
    from a FITS table containing separate date and time columns.

    Parameters
    ----------
    target_full_table : np.ndarray
        Numpy array representing a FITS table with at least two columns:
        column 0: date strings in "YYYY-MM-DD" format,
        column 1: time strings in "HH:MM:SS" format.

    Returns
    -------
    tuple of np.ndarray
        - datetime_list: np.ndarray of datetime.datetime objects combining date and time.
        - datetime_str: np.ndarray of strings in "YYYY-MM-DD HH:MM:SS" format.
    """
    data_array = np.array(target_full_table)
    datetime_str = np.char.add(data_array[:, 0], " ")
    datetime_str = np.char.add(datetime_str, data_array[:, 1])

    datetime_list = np.array([datetime.strptime(dt, "%Y-%m-%d %H:%M:%S") for dt in datetime_str])

    return datetime_list, datetime_str