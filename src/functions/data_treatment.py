from astropy.io import fits
import numpy as np
from scipy.ndimage import uniform_filter1d, gaussian_filter1d
from fastdtw import fastdtw
from datetime import datetime
from sklearn.linear_model import LinearRegression

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


def find_std(curve: np.ndarray, number_of_segments: int = 1, quantity: int = 1) -> float:
    """
    Find the std to use in this curve given the number of segments.

    Parameters
    ----------
    curve : np.ndarray
        List of points of the curve.

    number_of_segments : int, default=1
        Number of segments to separate the curve to find the std to be used.

    quantity : int, default=1
        Number os segments from the median to be taken to take the mean of the std.

    Returns
    -------
    float
        The calculated std for the curve.
    """
    if number_of_segments <= 0:
        raise ValueError("number_of_segments must be greater than 0.")
    if quantity <= 0:
        raise ValueError("quantity must be greater than 0.")
    if quantity > number_of_segments:
        raise ValueError("quantity must be smaller than number_of_segments")
    
    # Ignore first and last 15% of the curve
    # cut = int(0.15 * len(curve))
    # curve = curve[cut:-cut]

    # Split curve into `number_of_segments` segments as evenly as possible
    segments = np.array_split(curve, number_of_segments)

    # Calculate std for each segment
    stds = np.array([np.std(seg) for seg in segments])

    # Sort stds
    stds_sorted = np.sort(stds)

    # Find the median index
    mid = len(stds_sorted) // 2

    # Determine the slice indices for the chosen quantity centered around median
    half_q = quantity // 2
    if quantity % 2 == 1:
        # Odd quantity: perfectly centered
        start = max(mid - half_q, 0)
        end = min(mid + half_q + 1, len(stds_sorted))
    else:
        # Even quantity: pick the lower-centered set
        start = max(mid - half_q, 0)
        end = min(mid + half_q, len(stds_sorted))

    # Mean of selected std values
    return float(np.mean(stds_sorted[start:end]))


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


def find_common_intervals_weighted(intervals_list: list[dict], threshold: float) -> list[tuple[tuple[float, float], list]]:
    """
    Find intervals where the sum of weights of overlapping intervals exceeds a threshold.
    Also tracks which curves contributed to each interval.

    Parameters
    ----------
    intervals_list : list of dict
        Each element corresponds to a curve and contains:
            - "interval": list of tuples [(start, end), ...]
            - "weight": float, weight of this interval (0-100)
            - "curve": any, identifier of the curve
        
    threshold : float
        Minimum sum of weights for an interval to be included (0-100).

    Returns
    -------
    list of tuple[(start, end), list_of_curves]
        List of intervals where the sum of weights >= threshold, with the contributing curves.
    """
    # Generate events (position, weight change, curve id)
    events = []
    for entry in intervals_list:
        weight = entry["weight"]
        curve_id = entry["curve"]
        for start, end in entry["interval"]:
            events.append((start, +weight, curve_id))
            events.append((end, -weight, curve_id))

    # Sort events by position (start events before end events at same position)
    events.sort(key=lambda x: (x[0], -x[1]))

    intervals_common = []
    active_weight = 0
    current_start = None
    active_curves = set()

    for pos, change, curve_id in events:
        previous_weight = active_weight
        active_weight += change
        
        if change > 0:
            active_curves.add(curve_id)
        else:
            active_curves.discard(curve_id)
        
        # Entering a region where active_weight >= threshold
        if previous_weight < threshold and active_weight >= threshold:
            current_start = pos
            current_curves = active_curves.copy()
        # Exiting a region where active_weight >= threshold
        elif previous_weight >= threshold and active_weight < threshold:
            current_end = pos
            # Save the interval with the curves that were active in that region
            intervals_common.append(((current_start, current_end), list(current_curves)))
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


def is_linear_curve(y: np.ndarray, r2_threshold: float = 0.1, slope_tol: float = 6.5e-4) -> bool:
    """
    Determine if a curve is approximately linear or contains a peak/event.
    Also treats flat (no-slope) noisy data as linear.
    
    Parameters
    ----------
    y : np.ndarray
        1D array of values (the curve)

    r2_threshold : float, default=0.1
        Minimum R² to consider it approximately linear.

    slope_tol : float, default = 6.5e-4
        Absolute slope threshold below which the curve is considered flat (and thus linear),
        even if the R² value is low. Helps to classify nearly constant noisy signals as linear.
    
    Returns
    -------
    bool
        True if the curve is approximately linear, False if it contains a peak/event.
    """
    n = len(y)
    if n < 20:
        return True

    x = np.arange(n).reshape(-1, 1)
    model = LinearRegression().fit(x, y)
    r2 = model.score(x, y)
    slope = model.coef_[0]

    # print("Slope: ", abs(slope), slope_tol, abs(slope) < slope_tol)
    # If slope is very small -> nearly constant -> consider linear
    if abs(slope) < slope_tol:
        return True
    
    # print("R²: ", r2, r2_threshold, r2 > r2_threshold)

    return r2 > r2_threshold

# def is_linear_curve(
#     y: np.ndarray,
#     r2_threshold: float = 0.1,
#     smooth_sigma: float = 2.0
# ) -> bool:
#     """
#     Determine if a curve is approximately linear or contains a peak/event.
#     Uses Gaussian smoothing to reduce noise before checking.
#     Slope check is removed — R² alone is used after smoothing.
    
#     Parameters
#     ----------
#     y : np.ndarray
#         1D array of values (the curve)

#     r2_threshold : float, default=0.1
#         Minimum R² to consider it approximately linear.

#     smooth_sigma : float, default=2.0
#         Standard deviation for Gaussian smoothing. Higher values smooth more aggressively.
    
#     Returns
#     -------
#     bool
#         True if the curve is approximately linear, False if it contains a peak/event.
#     """
#     n = len(y)
#     if n < 20:
#         return True

#     # 1. Smooth the curve
#     y_smooth = gaussian_filter1d(y, sigma=smooth_sigma)

#     # 2. Fit a linear regression to the smoothed data
#     x = np.arange(n).reshape(-1, 1)
#     model = LinearRegression().fit(x, y_smooth)
#     r2 = model.score(x, y_smooth)

#     print(r2, r2_threshold, r2 > r2_threshold)

#     # 3. Decide based on R²
#     return r2 > r2_threshold