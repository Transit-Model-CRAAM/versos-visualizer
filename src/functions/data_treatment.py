import numpy as np
import pathlib
import requests
import zipfile
import io
import time

from bs4 import BeautifulSoup
from astropy.io import fits
from scipy.ndimage import uniform_filter1d, gaussian_filter1d
from fastdtw import fastdtw
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from typing import Union, Sequence, List, Tuple, Optional


# ======== Funções de obtenção dos dados ========


def get_local_path(date_obj: datetime) -> Optional[str]:
    """
    Checks if the FITS file for a given date already exists in the local directory structure.

    Parameters
    ----------
    date_obj : datetime
        The date object to check in the local storage.

    Returns
    -------
    Optional[str]
        The absolute path to the .fits file if it exists, otherwise None.
    """
    # Base directory for the project
    base_dir = pathlib.Path("solar_data")
    
    # Standardized filename: POEMAS_derived_1s_FITS_YYYY_MM_DD.fits
    filename = f"POEMAS_derived_1s_FITS_{date_obj.strftime('%Y_%m_%d')}.fits"
    
    # Full path: solar_data/YYYY/MM/DD/POEMAS_derived_1s_FITS_YYYY_MM_DD.fits
    file_path = base_dir / date_obj.strftime("%Y/%m/%d") / filename
    
    # Check if the exact file exists
    if file_path.exists():
        return str(file_path.resolve())
    
    return None


def find_remote_zip_url(date_obj: datetime) -> Optional[str]:
    """
    Crawl the remote dataset endpoint to find the full URL of the .zip file for a specific date.

    Parameters
    ----------
    date_obj : datetime
        The date object used to build the directory URL to be crawled.

    Returns
    -------
    Optional[str]
        The full URL for the .zip file if found (matching the POEMAS prefix), otherwise None.
    """
    # Base URL for the POEMAS products
    base_url = "https://datasets.linea.org.br/craam/products/poemas/"
    
    # Construct the specific directory URL: .../YYYY/MM/DD/
    folder_url = f"{base_url}{date_obj.strftime('%Y/%m/%d/')}"
    
    try:
        # Request the directory page
        response = requests.get(folder_url, timeout=10)
        
        # If the page doesn't exist (404), there's no data for this day
        if response.status_code != 200:
            return None
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Search for all <a> tags (links)
        for link in soup.find_all('a'):
            href = link.get('href')
            
            # Check if the link starts with the desired prefix and ends with .zip
            if href and href.startswith("POEMAS_derived_1s_FITS_") and href.endswith(".zip"):
                # Return the full URL by joining the folder path with the filename
                return f"{folder_url}{href}"
                
    except requests.exceptions.RequestException:
        # If there's a connection error, return None
        return None

    return None


def download_and_extract_zip(url: str, date_obj: datetime, retries: int = 3) -> Optional[str]:
    """
    Downloads the .zip file with retry logic, validates integrity, extracts 
    the .fits file, and renames it to a standardized format.

    Parameters
    ----------
    url : str
        The remote URL of the .zip file.
    date_obj : datetime
        The date object used for directory and filename standardization.
    retries : int, optional
        Number of times to attempt the download if it fails (default is 3).

    Returns
    -------
    Optional[str]
        The absolute path to the .fits file, or None if all attempts fail.
    """
    base_dir = pathlib.Path("solar_data")
    target_folder = base_dir / date_obj.strftime("%Y/%m/%d")
    standardized_name = f"POEMAS_derived_1s_FITS_{date_obj.strftime('%Y_%m_%d')}.fits"
    final_path = target_folder / standardized_name

    for attempt in range(retries):
        try:
            target_folder.mkdir(parents=True, exist_ok=True)

            # Download attempt
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                raise requests.RequestException("Download failed")

            zip_data = io.BytesIO(response.content)

            with zipfile.ZipFile(zip_data) as z:
                # CRC Check
                if z.testzip() is not None:
                    raise zipfile.BadZipFile("Corrupted ZIP data")
                
                fits_in_zip = [f for f in z.namelist() if f.endswith('.fits')]
                if not fits_in_zip:
                    return None
                
                # Write to disk
                with z.open(fits_in_zip[0]) as source, open(final_path, "wb") as target:
                    target.write(source.read())

            return str(final_path.resolve())

        except (requests.RequestException, zipfile.BadZipFile, IOError) as e:
            # Clean up partial file if it exists
            if final_path.exists():
                final_path.unlink()
            
            # If it's the last attempt, we give up
            if attempt == retries - 1:
                return None
            
            # Wait a bit before retrying (exponential backoff could be used, 
            # but a fixed 2s is enough for most cases)
            time.sleep(2)
            
    return None


def fetch_data_for_date(date_obj: datetime) -> Optional[str]:
    """
    High-level orchestrator for a single day. Checks the local disk first, 
    then the remote server. If found online, it downloads and extracts the file.

    Parameters
    ----------
    date_obj : datetime
        The target date for data acquisition.

    Returns
    -------
    Optional[str]
        The absolute local path to the .fits file, or None if the data is unavailable.
    """
    # Check if the file already exists locally
    local_path = get_local_path(date_obj)
    if local_path:
        return local_path

    # If not local, try to find the remote URL using the crawler
    remote_url = find_remote_zip_url(date_obj)
    if not remote_url:
        return None

    # If URL is found, download, extract and rename the file
    # This function already returns the absolute path of the new file
    final_local_path = download_and_extract_zip(remote_url, date_obj)
    
    return final_local_path


def prepare_versos_dataset(target_date_str: str) -> Tuple[List[str], Optional[str]]:
    """
    Main function to prepare the dataset for analysis. It enforces the 'gatekeeper' 
    rule for the target date and searches for the nearest 6 background days.

    Parameters
    ----------
    target_date_str : str
        The primary date for analysis in 'YYYY-MM-DD' format.

    Returns
    -------
    all_files : List[str]
        A list of paths for the 7 files found (Target + 6 Neighbors).
    target_file_to_load : Optional[str]
        The specific path for the target date file. Returns None if target date is missing.

    Notes
    -----
    The function alternates between future and past days (±1, ±2...) until 6 
    background days are found or the 30-day limit is reached.
    """
    # Convert input string to datetime object
    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    except ValueError:
        return [], None

    # Gatekeeper: Check for the target date first
    target_path = fetch_data_for_date(target_date)
    
    if not target_path:
        # If the main event data is missing, we stop immediately
        return [], None

    # Background search: Find 6 closest existing days
    all_files = [target_path]
    found_background = []
    offset = 1
    max_range = 30  # Search limit in days

    while len(found_background) < 6 and offset <= max_range:
        # Check future day (+offset)
        future_day = target_date + timedelta(days=offset)
        future_path = fetch_data_for_date(future_day)
        if future_path:
            found_background.append(future_path)
        
        # Check if we still need more before checking the past day
        if len(found_background) < 6:
            # Check past day (-offset)
            past_day = target_date - timedelta(days=offset)
            past_path = fetch_data_for_date(past_day)
            if past_path:
                found_background.append(past_path)
        
        offset += 1

    # Combine everything into one list
    all_files.extend(found_background)

    return all_files, target_path


# ======== Funções de pré-processamento ========

def load_fits_data(fits_path: str, idx: str = "TBL45") -> Tuple[np.ndarray, np.recarray, str]:
    """
    Read and load the fits data.

    Parameters
    ----------
    fits_path : str
        Path for the file to be opened.

    idx : str, default="TBL45"
        The position of the curve to be loaded in the fits file. Possible values are::

            - "TBL45"
            - "TBR45"
            - "TBL90"
            - "TBR90"

    Returns
    -------
    np.ndarray
        Values of the selected type of curve.

    np.recarray
        The fits table of that file, with only "date" and "time" columns.

    str
        The date of the event (YYYY-MM-DD format)
    """
    with fits.open(fits_path) as hdul:
        tabela = hdul[1].data

        # Extrai o valor da coluna desejada
        data = tabela[idx]

        # Extrai o dia do primeiro registro do ISO_DATETIME
        iso_datetime = tabela["ISO_DATETIME"][0]
        if isinstance(iso_datetime, bytes):
            iso_datetime = iso_datetime.decode()
        day = iso_datetime.split("T")[0]

        # Cria uma tabela reduzida apenas com "date" e "time"
        # Separa "date" e "time" do ISO_DATETIME
        dates = []
        times = []
        for dt in tabela["ISO_DATETIME"]:
            if isinstance(dt, bytes):
                dt = dt.decode()
            date_part, time_part = dt.split("T")
            dates.append(date_part)
            times.append(time_part[:8])  # Garante formato HH:MM:SS

        # Monta uma nova tabela numpy com "date" e "time"
        full_table = np.rec.fromarrays([dates, times], names=("Date", "Time"))

        return data, full_table, day
    

def build_curve_time_arrays_from_target_day(
    curve_tables: list,
    target_day: str
) -> List[np.ndarray]:
    """
    Generate timestamp arrays for each FITS table using a fixed target day.

    This function ignores the original 'Date' column in each FITS table and
    combines the provided `target_day` with each row's 'Time' field to create
    new datetime values. These datetimes are then converted to Unix timestamps
    (float seconds since epoch).

    Parameters
    ----------
    curve_tables : list
        List of FITS_rec tables containing at least a 'Time' column.
        The 'Time' field must be byte strings (e.g., b'12:36:01').

    target_day : str
        Date string in ISO format: "YYYY-MM-DD".

    Returns
    -------
    List[np.ndarray]
        A list where each element is a 1D NumPy array (dtype=float64)
        containing Unix timestamps corresponding to the times of each
        input table, using `target_day` as the date.
    """

    result = []

    for table in curve_tables:
        # Decode byte times → string
        time_strings = [
            t.decode() if isinstance(t, bytes) else str(t)
            for t in table["Time"]
        ]

        # Combine target_day with time and convert to datetime
        timestamps = np.array(
            [
                datetime.fromisoformat(f"{target_day}T{time_str}").timestamp()
                for time_str in time_strings
            ],
            dtype=float
        )

        result.append(timestamps)

    return result


def clip_outliers_iqr(arr: np.ndarray, factor: float = 1.5) -> np.ndarray:
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


def remove_low_intensity_artifacts(
    arr: np.ndarray, 
    arr_datetime: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Remove constant segments and low intensity artifacts from the curve.

    Parameters
    ----------
    arr : np.ndarray
        Input light curve data as a 1D array.
    arr_datetime : np.ndarray
        Datetime or timestamp array corresponding to arr.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        Filtered versions of (arr, arr_datetime).
    """
    n = len(arr)
    if n < 40:
        return arr, arr_datetime

    # Remove constant segments at the start and end
    # np.diff finds where the value changes
    diffs = np.diff(arr)
    
    # Start: first index where value actually changes
    start_idx = 0
    non_zero_start = np.where(diffs != 0)[0]
    if len(non_zero_start) > 0:
        start_idx = non_zero_start[0] + 1

    # End: last index where value actually changes
    end_idx = n
    non_zero_end = np.where(diffs != 0)[0]
    if len(non_zero_end) > 0:
        end_idx = non_zero_end[-1] + 1

    # Apply constant trim
    arr = arr[start_idx:end_idx]
    arr_datetime = arr_datetime[start_idx:end_idx]
    
    # Re-check length after trimming
    n = len(arr)
    if n < 40:
        return arr, arr_datetime

    # Statistical artifact removal (Head vs Tail)
    chunk_size = max(1, int(n * 0.025))
    head = arr[:chunk_size]
    tail = arr[-chunk_size:]

    mean_h, std_h = np.mean(head), np.std(head)
    mean_t, std_t = np.mean(tail), np.std(tail)

    if abs(mean_h - mean_t) > 2 * max(std_h, std_t):
        ref_mean = max(mean_h, mean_t)
        ref_std = std_h if mean_h > mean_t else std_t
        threshold = ref_mean - 3 * ref_std
        
        mask = arr >= threshold
        return arr[mask], arr_datetime[mask]

    return arr, arr_datetime


def preprocess_curve(
    arr: np.ndarray,
    arr_datetimes: Optional[np.ndarray] = None,
    smooth_window: int = 125,
    n_apply_smooth: int = 2,
    target: bool = True,
) -> Tuple[np.ndarray, Optional[np.ndarray]]:
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

    arr_datetimes : np.ndarray, optional
        Input datetimes of the lightcurve as a 1D array.

    smooth_window : int, default=125
        Number of neighbours to apply the smoothing.

    n_apply_smooth : int, default=2
        Number of iterations to apply the smoothing with `smooth_window` neighbours.

    target : bool, default=True
        Boolean to indicate if the curve is the target (event) or a background curve.

    Returns
    -------
    Tuple[np.ndarray, Optional[np.ndarray]]
        - Preprocessed light curve, same shape as input.
        - Datetimes after preprocessing (if `target` is False), or unchanged datetimes.
    """
    if not target:
        arr, arr_datetimes = remove_low_intensity_artifacts(arr, arr_datetimes)
    arr = clip_outliers_iqr(arr, factor=1.5)
    arr = z_score_norm(arr)
    arr = apply_smooth(arr, smooth_window, n_apply_smooth)
    return arr, arr_datetimes


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


def _to_timestamp_array(datetime_array: Union[Sequence, np.ndarray]) -> np.ndarray:
    """
    Convert a sequence of datetime representations to Unix timestamps.

    This function converts supported datetime-like inputs into a
    NumPy array of float64 values representing seconds since the
    Unix epoch (1970-01-01 00:00:00 UTC).

    Supported input element types
    -----------------------------
    - datetime.datetime
    - str (ISO 8601 format, e.g. "YYYY-MM-DD HH:MM:SS" or
      "YYYY-MM-DDTHH:MM:SS", optionally with microseconds)
    - numpy.datetime64
    - int or float (assumed to already represent Unix timestamps in seconds)

    Parameters
    ----------
    datetime_array : sequence or numpy.ndarray
        A sequence of datetime-like objects or numeric timestamps.
        The sequence must be one-dimensional and non-empty.
        All elements must be of the same supported type.

    Returns
    -------
    numpy.ndarray
        One-dimensional array of dtype float64 containing Unix
        timestamps in seconds.

    Raises
    ------
    TypeError
        If the element type is not supported.

    ValueError
        If ISO string parsing fails.
    """

    if len(datetime_array) == 0:
        return np.array([], dtype=float)

    first = datetime_array[0]

    if isinstance(first, datetime):
        return np.array(
            [dt.timestamp() for dt in datetime_array],
            dtype=float
        )

    elif isinstance(first, str):
        return np.array(
            [datetime.fromisoformat(dt).timestamp() for dt in datetime_array],
            dtype=float
        )

    elif isinstance(first, np.datetime64):
        dt_objects = (
            np.asarray(datetime_array)
            .astype("datetime64[s]")
            .astype(datetime)
        )
        return np.array(
            [dt.timestamp() for dt in dt_objects],
            dtype=float
        )

    elif isinstance(first, (int, float, np.integer, np.floating)):
        # Already Unix timestamps
        return np.asarray(datetime_array, dtype=float)

    else:
        raise TypeError(
            f"Unsupported datetime type: {type(first)}"
        )


def interpolate_gated_to_zero(
    target_datetime: Union[np.ndarray, list],
    curve_datetime: Union[np.ndarray, list],
    curve_data: Union[np.ndarray, list],
    max_gap_seconds: float = 300.0
) -> np.ndarray:
    """
    Interpolate curve data to target timestamps, forcing gaps to zero.

    Parameters
    ----------
    target_datetime : array-like
        Datetime array defining the desired time grid.
    curve_datetime : array-like
        Datetime array corresponding to curve_data.
    curve_data : array-like
        Numeric values associated with curve_datetime.
    max_gap_seconds : float, optional
        Maximum allowed gap in seconds between a target timestamp and the 
        nearest available data point before forcing the value to zero.

    Returns
    -------
    np.ndarray
        Array of interpolated values. Points exceeding `max_gap_seconds` 
        from any original data point are set to 0.
    """
    target_ts = _to_timestamp_array(target_datetime)
    curve_ts = _to_timestamp_array(curve_datetime)
    curve_data = np.asarray(curve_data, dtype=float)

    order = np.argsort(curve_ts)
    curve_ts = curve_ts[order]
    curve_data = curve_data[order]

    # Standard linear interpolation
    interpolated = np.interp(target_ts, curve_ts, curve_data)

    # Apply distance-based mask
    # searchsorted finds the insertion index to maintain order
    idx = np.searchsorted(curve_ts, target_ts)
    
    # Check distance to neighbors on both sides
    idx_left = np.clip(idx - 1, 0, len(curve_ts) - 1)
    idx_right = np.clip(idx, 0, len(curve_ts) - 1)
    
    dist_left = np.abs(target_ts - curve_ts[idx_left])
    dist_right = np.abs(target_ts - curve_ts[idx_right])
    min_dist = np.minimum(dist_left, dist_right)

    interpolated[min_dist > max_gap_seconds] = 0

    return interpolated


def interpolate_curve_to_target_time(
    target_datetime: Union[np.ndarray, list],
    curve_datetime: Union[np.ndarray, list],
    curve_data: Union[np.ndarray, list],
    method: str = "linear"
) -> np.ndarray:
    """
    Interpolate a curve so that its values are aligned to the
    datetime grid of a target curve.

    The interpolation is performed in timestamp space (seconds since epoch).

    Parameters
    ----------
    target_datetime : array-like
        Datetime array defining the desired time grid.

    curve_datetime : array-like
        Datetime array corresponding to curve_data.

    curve_data : array-like
        Numeric values associated with curve_datetime.

    method : str, optional
        Interpolation method. Currently only "linear" is supported.

    Returns
    -------
    np.ndarray
        Array of interpolated values aligned to target_datetime.
        Values outside the original curve time range are filled with np.nan.

    Raises
    ------
    ValueError
        If interpolation method is not supported.

    TypeError
        If datetime format is unsupported.
    """

    if method != "linear":
        raise ValueError("Only 'linear' interpolation is supported.")

    # Convert datetimes to timestamps
    target_ts = _to_timestamp_array(target_datetime)
    curve_ts = _to_timestamp_array(curve_datetime)

    curve_data = np.asarray(curve_data, dtype=float)

    if len(curve_ts) != len(curve_data):
        raise ValueError(
            "curve_datetime and curve_data must have the same length."
        )

    # Ensure curve is sorted by time
    order = np.argsort(curve_ts)
    curve_ts = curve_ts[order]
    curve_data = curve_data[order]

    interpolated = np.interp(
        target_ts,
        curve_ts,
        curve_data,
        left=0,
        right=0
    )

    return interpolated


def get_closest_datetime_index(
    datetime_array: np.ndarray,
    target_datetime_str: str,
    fmt: str = "%Y-%m-%d %H:%M:%S"
) -> int:
    """
    Returns the index of the closest datetime in datetime_array
    to the given target datetime string.

    Parameters
    ----------
    datetime_array : np.ndarray
        Array of datetime.datetime objects.

    target_datetime_str : str
        Datetime string in the given format (default: "%Y-%m-%d %H:%M:%S").

    fmt : str
        Datetime format used for parsing the string.

    Returns
    -------
    int
        Index of the closest datetime in the array.
    """

    target_dt = datetime.strptime(target_datetime_str, fmt)

    target_ts = target_dt.timestamp()
    array_ts = np.array([dt.timestamp() for dt in datetime_array])

    # Find index with the time closest to target
    idx = np.argmin(np.abs(array_ts - target_ts))

    return int(idx)


# ======== Função FastDTW ========

def calcular_fastdtw(idx: int, curva_interp: np.ndarray, target_interp: np.ndarray) -> Tuple[int, float]:
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
    Tuple[int, float]
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


def merge_intervals(intervals: list[Tuple[float, float]], gap: int = 5) -> list[Tuple[float, float]]:
    """
    Merge overlapping or close intervals in a list.

    Parameters
    ----------
    intervals : list of Tuple[float, float]
        List of intervals, each represented as a tuple (start, end).

    gap : int, default=5
        Maximum allowed gap between intervals to merge them.

    Returns
    -------
    list of Tuple[float, float]
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


def find_common_intervals_weighted(intervals_list: list[dict], threshold: float) -> list[Tuple[Tuple[float, float], list]]:
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
    list of Tuple[(start, end), list_of_curves]
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


def generate_datetime_list(target_full_table: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
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

# ======== Funções auxiliares ========

def to_list(arr: np.ndarray) -> list:
    """
    Converts a numpy array to a contiguous Python list.

    Parameters
    ----------
    arr : np.ndarray
        Input numpy array.

    Returns
    -------
    list
        Contiguous Python list.
    """
    return np.ascontiguousarray(arr).tolist()

def fits_table_to_list_of_lists(fits_table: np.recarray) -> list[list]:
    """
    Converts a FITS table to a list of lists.

    Parameters
    ----------
    fits_table : np.recarray
        FITS table object.

    Returns
    -------
    list of list
        List of rows, each row as a list.
    """
    return [list(row) for row in fits_table]