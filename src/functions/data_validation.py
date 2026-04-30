import pathlib
import requests
import gzip
import shutil
import re
import json
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

import pandas as pd
import numpy as np
from scipy.io import readsav
from datetime import datetime, timedelta
import xarray as xr


def find_validation_file_url(base_folder_url: str, date_obj: datetime) -> Optional[str]:
    """
    Crawls a monthly directory to find a filename matching the target date
    using regex patterns to identify multiple date formats.

    Parameters
    ----------
    base_folder_url : str
        The URL of the monthly directory to be crawled.
    date_obj : datetime
        The target date to look for within the file listing.

    Returns
    -------
    Optional[str]
        The full remote URL of the matched file, or None if no match is found.
    """
    try:
        response = requests.get(base_folder_url, timeout=15)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. 20131105 (YYYYMMDD)
        # 2. 05NOV13 (DDMonYY)
        # 3. 131105   (YYMMDD) - Common in Nobeyama/NoRP
        patterns = [
            date_obj.strftime("%Y%m%d"),
            date_obj.strftime("%d%b%y"),
            date_obj.strftime("%y%m%d")
        ]

        regex_pattern = re.compile(f"({'|'.join(patterns)})", re.IGNORECASE)

        for link in soup.find_all('a'):
            href = link.get('href')
            if not href:
                continue

            # Check if any of our date patterns exist in the filename
            if regex_pattern.search(href):
                # Clean the URL from query strings (like ?C=N;O=D)
                clean_filename = href.split('?')[0]
                # Return the absolute URL
                return f"{base_folder_url.rstrip('/')}/{clean_filename}"

    except Exception as e:
        print(f"Crawler error at {base_folder_url}: {e}")
        return None

    return None


def fetch_validation_data(observatory: str, date_str: str) -> Optional[str]:
    """
    Downloads and prepares solar radio data from specific observatories 
    (Learmonth, Sagamore Hill, Palehua, or Nobeyama) for validation purposes.

    Parameters
    ----------
    observatory : str
        The name of the observatory: "learmonth", "sagamore-hill", "palehua", "san-vito", or "nobeyama".
    date_str : str
        The date in "YYYY-MM-DD" format.

    Returns
    -------
    Optional[str]
        The absolute path to the downloaded (and extracted) file, or None if failed.

    Notes
    -----
    The function uses a regex-based crawler to identify the correct filename 
    within the remote monthly directory, supporting various naming conventions.
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        yyyy, mm, dd = date_obj.strftime("%Y"), date_obj.strftime("%m"), date_obj.strftime("%d")

        # Define destination directory
        target_dir = pathlib.Path("validation_data") / yyyy / mm / dd

        # Define the monthly endpoint to crawl
        if observatory in ["learmonth", "sagamore-hill", "palehua", "san-vito"]:
            base_url = (f"https://www.ngdc.noaa.gov/stp/space-weather/solar-data/"
                        f"solar-features/solar-radio/rstn-1-second/{observatory}/{yyyy}/{mm}/")
            is_gzip = True
        elif observatory == "nobeyama":
            base_url = f"https://solar.nro.nao.ac.jp/norp/xdr/{yyyy}/{mm}/"
            is_gzip = False
        else:
            return None

        remote_url = find_validation_file_url(base_url, date_obj)
        if not remote_url:
            return None

        # Handling the case where filenames might have multiple dots (e.g., file.lea.gz)
        parts = remote_url.split('/')[-1].split('.')
        # If it's gzip, the extension we want is usually the one before '.gz'
        ext = parts[-2] if is_gzip and len(parts) > 2 else parts[-1]
        
        local_filename = f"{observatory}_{date_obj.strftime('%Y%m%d')}.{ext}"
        final_path = target_dir / local_filename

        return download_and_handle_file(remote_url, final_path, is_gzip)

    except Exception as e:
        print(f"Error preparing validation data for {observatory} on {date_str}: {e}")
        return None


def download_and_handle_file(url: str, final_path: pathlib.Path, is_gzip: bool) -> Optional[str]:
    """
    Helper function to download a file. If it's a .gz, it extracts the content 
    and saves it to the final_path. Otherwise, it saves the raw content.

    Parameters
    ----------
    url : str
        The full remote URL of the file to download.
    final_path : pathlib.Path
        The local path object where the file should be saved.
    is_gzip : bool
        Flag indicating if the source file is gzipped and needs extraction.

    Returns
    -------
    Optional[str]
        The absolute path to the saved file as a string, or None if failed.
    """
    try:
        response = requests.get(url, timeout=30, stream=True)
        if response.status_code != 200:
            return None

        final_path.parent.mkdir(parents=True, exist_ok=True)

        if is_gzip:
            with gzip.GzipFile(fileobj=response.raw) as g:
                with open(final_path, "wb") as f_out:
                    shutil.copyfileobj(g, f_out)
        else:
            with open(final_path, "wb") as f_out:
                f_out.write(response.content)

        return str(final_path.resolve())

    except Exception as e:
        print(f"Failed to process file from {url}: {e}")
        if final_path.exists():
            final_path.unlink()
        return None
    

def norp_day_time_to_datetime(day_array: np.ndarray, time_ms_array: np.ndarray) -> List[datetime]:
    """
    Converts NORP DAY and TIME arrays to Python datetime objects.

    Parameters
    ----------
    day_array : array-like
        Days since 1978-12-31.
    time_ms_array : array-like
        Milliseconds since 00:00:00 of that day.

    Returns
    -------
    List[datetime]
        A list of datetime objects corresponding to the observation timestamps.
    """
    # Base date for Nobeyama Radio Polarimeters (NoRP) data
    base = datetime(1978, 12, 31)

    timestamps = []
    for d, t in zip(day_array, time_ms_array):
        # The arrays usually come from IDL as floats or ints
        ts = base + timedelta(days=int(d), milliseconds=int(t))
        timestamps.append(ts)

    return timestamps


def load_validation_data(observatory: str, date_str: str) -> Tuple[Optional[List[datetime]], Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Loads and extracts solar radio data from validation files based on the 
    observatory and date.

    Parameters
    ----------
    observatory : str
        The name of the observatory: "learmonth", "sagamore-hill", "palehua", "san-vito", or "nobeyama".
    date_str : str
        The date in "YYYY-MM-DD" format.

    Returns
    -------
    timestamps : List[datetime] or None
        List of converted datetime objects for the observations.
    freq_intensities : np.ndarray or None
        Array containing frequency intensities (fi).
    frequency_list : np.ndarray or None
        Array of the observed frequencies (freq).

    Notes
    -----
    The function searches for any file starting with the observatory name in the 
    target directory, making it extension-agnostic.
    """
    try:
        # Parse date to locate the folder
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        yyyy, mm, dd = date_obj.strftime("%Y"), date_obj.strftime("%m"), date_obj.strftime("%d")

        # Local directory where files are stored
        base_dir = pathlib.Path("validation_data") / yyyy / mm / dd

        if not base_dir.exists():
            print(f"Directory not found: {base_dir}")
            return None, None, None

        # Search for any file that starts with the observatory name
        matching_files = list(base_dir.glob(f"{observatory}_*"))

        if not matching_files:
            print(f"No validation file found for {observatory} in {base_dir}")
            return None, None, None

        # Take the first match
        file_path = matching_files[0]

        if observatory == "nobeyama":
            # Load IDL Save file
            data = readsav(str(file_path.resolve()))

            # Extract data structure
            frequency_list = data['freq']
            tim = data["tim"]
            freq_intensities = data["fi"]

            # Extract time and day components
            ms = tim["TIME"]
            day = tim["DAY"]

            # Convert to Python datetimes
            timestamps = norp_day_time_to_datetime(day, ms)

            return timestamps, freq_intensities, frequency_list
        
        elif observatory in ["learmonth", "sagamore-hill", "palehua", "san-vito"]:
            # Standard frequency list for the RSTN network
            frequencies_ghz = np.array([
                0.245, 0.410, 0.610, 1.415, 2.695, 4.995, 8.800, 15.400
            ])

            # Define fixed-width column intervals to handle irregular spacing/missing data
            # Column 0: ID (4 chars) + Timestamp (14 chars) = 18 total width
            # Data columns: 9 subsequent blocks of 7 characters each for intensities
            col_intervals = [(0, 18)] + [(18 + i*7, 18 + (i+1)*7) for i in range(9)]

            df = pd.read_fwf(
                file_path, 
                colspecs=col_intervals, 
                header=None, 
                engine='python'
            )

            # Process Timestamps: Remove the 4-character observatory prefix and convert
            # 'errors=coerce' ensures corrupt lines are handled as NaT
            raw_timestamps = df[0].str.strip().str[4:]
            timestamps = pd.to_datetime(raw_timestamps, format='%Y%m%d%H%M%S', errors='coerce').tolist()

            # Intensities: Extract data columns (indices 1 to 8, matching the 8 frequencies)
            # Convert to numpy array for consistency with NoRP output
            freq_intensities = df.iloc[:, 1:9].values

            return timestamps, freq_intensities, frequencies_ghz

        return None, None, None

    except Exception as e:
        print(f"Error loading validation data for {observatory} on {date_str}: {e}")
        return None, None, None
    

def fetch_goes_data(date_str: str) -> Optional[str]:
    """
    Downloads GOES X-ray flux data (L2 1-minute science averages) from NCEI
    and saves it to the validation_data directory structure.

    Parameters
    ----------
    date_str : str
        The date in "YYYY-MM-DD" format.

    Returns
    -------
    Optional[str]
        The absolute path to the downloaded .nc file, or None if failed.
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        yyyy, mm, dd = date_obj.strftime("%Y"), date_obj.strftime("%m"), date_obj.strftime("%d")
        yyyymmdd = date_obj.strftime("%Y%m%d")

        target_dir = pathlib.Path("validation_data") / yyyy / mm / dd
        final_path = target_dir / f"goes_{yyyymmdd}.nc"

        # Define the science-quality repository URL
        # For years 2011-2012, we use GOES-15
        base_url = (f"https://www.ncei.noaa.gov/data/goes-space-environment-monitor/access/"
                    f"science/xrs/goes15/xrsf-l2-avg1m_science/{yyyy}/{mm}/")

        response = requests.get(base_url, timeout=15)
        if response.status_code != 200:
            print(f"Directory not found: {base_url}")
            return None

        # Crawler to find the file containing f"d{YYYYMMDD}"
        soup = BeautifulSoup(response.text, 'html.parser')
        target_pattern = f"d{yyyymmdd}"
        remote_filename = None
        
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and target_pattern in href and href.endswith('.nc'):
                remote_filename = href
                break
        
        if not remote_filename:
            print(f"No GOES file found for date pattern {target_pattern} at {base_url}")
            return None

        # Download the file
        download_url = base_url + remote_filename
        target_dir.mkdir(parents=True, exist_ok=True)
        
        resp = requests.get(download_url, timeout=30)
        if resp.status_code == 200:
            with open(final_path, "wb") as f:
                f.write(resp.content)
            return str(final_path.resolve())
        
        return None

    except Exception as e:
        print(f"Error fetching GOES data from NCEI: {e}")
        return None


def load_goes_data(date_str: str) -> Tuple[Optional[List[datetime]], Optional[pd.DataFrame]]:
    """
    Loads GOES X-ray science data from a local NetCDF file.

    Parameters
    ----------
    date_str : str
        The date in "YYYY-MM-DD" format.

    Returns
    -------
    timestamps : list of datetime or None
    goes_data : pd.DataFrame or None (columns: xrsa_flux, xrsb_flux)
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        yyyy, mm, dd = date_obj.strftime("%Y"), date_obj.strftime("%m"), date_obj.strftime("%d")
        yyyymmdd = date_obj.strftime("%Y%m%d")

        file_path = pathlib.Path("validation_data") / yyyy / mm / dd / f"goes_{yyyymmdd}.nc"

        if not file_path.exists():
            return None, None

        # Using xarray to open the science NetCDF
        ds = xr.open_dataset(file_path)

        # In science L2 files, time is often 'time' or 'time_tag'
        time_var = 'time' if 'time' in ds.coords else 'time_tag'
        
        # Convert cftime or numpy datetime to standard python datetime
        timestamps = pd.to_datetime(ds[time_var].values).to_pydatetime().tolist()

        # Science files use xrsa_flux and xrsb_flux names
        df_flux = pd.DataFrame({
            'xrsa_flux': ds.xrsa_flux.values,
            'xrsb_flux': ds.xrsb_flux.values
        })

        ds.close()
        return timestamps, df_flux

    except Exception as e:
        print(f"Error loading GOES science data for {date_str}: {e}")
        return None, None
    

def get_all_data_for_date(date_str: str) -> dict:
    """
    Orchestrates the loading and downloading of all validation data (Radio and GOES)
    for a specific date.

    Parameters
    ----------
    date_str : str
        The target date in "YYYY-MM-DD" format.

    Returns
    -------
    dict
        A dictionary containing data for 'palehua', 'sagamore-hill', 'learmonth', 
        'nobeyama', and 'goes'. 
        Each radio entry contains (timestamps, intensities, frequencies).
        The 'goes' entry contains (timestamps, flux_dataframe).
    """
    all_data = {
        "palehua": None,
        "sagamore-hill": None,
        "learmonth": None,
        "san-vito": None,
        "nobeyama": None,
        "goes": None
    }

    radio_observatories = ["palehua", "sagamore-hill", "learmonth", "san-vito", "nobeyama"]

    print(f"--- Processing data for {date_str} ---")

    # 1. Process Radio Observatories
    for obs in radio_observatories:
        # Lógica para Nobeyama: 1 dia à frente
        current_target_date = date_str
        if obs == "nobeyama":
            current_date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            next_day_obj = current_date_obj + timedelta(days=1)
            current_target_date = next_day_obj.strftime("%Y-%m-%d")
            print(f"[{obs.upper()}] Adjusted date for Japanese time: {current_target_date}")

        # Attempt to load from disk first
        ts, fi, fl = load_validation_data(obs, current_target_date)

        # If data is missing, attempt to fetch and reload
        if ts is None:
            print(f"[{obs.upper()}] Data not found on disk. Fetching...")
            fetch_path = fetch_validation_data(obs, current_target_date)
            
            if fetch_path:
                print(f"[{obs.upper()}] Download successful. Loading...")
                ts, fi, fl = load_validation_data(obs, current_target_date)
            else:
                print(f"[{obs.upper()}] Failed to fetch data from remote server.")

        all_data[obs] = {
            "timestamps": ts,
            "freq_intensities": fi,
            "frequency_list": fl
        }

    # 2. Process GOES Data (Mantém a data original)
    ts_goes, df_goes = load_goes_data(date_str)

    if ts_goes is None:
        print("[GOES] Science data not found on disk. Fetching from NCEI...")
        fetch_path_goes = fetch_goes_data(date_str)
        
        if fetch_path_goes:
            print("[GOES] Download successful. Loading NetCDF...")
            ts_goes, df_goes = load_goes_data(date_str)
        else:
            print("[GOES] Failed to fetch data from NCEI.")

    all_data["goes"] = {
        "timestamps": ts_goes,
        "data": df_goes
    }

    print(f"--- Finished processing {date_str} ---")
    return all_data


def save_event_times_to_json(
    day: str, 
    start_times: list, 
    end_times: list, 
    file_path: str = "temp/events.json"
) -> None:
    """
    Converte listas de tempos em uma lista de dicionários com timestamps completos.

    Pega listas de horários e uma data base, concatenando-as para formar
    timestamps completos (YYYY-MM-DD HH:MM:SS) nas chaves 'start' e 'end'.

    Parameters
    ----------
    start_times : list of str
        Lista contendo os horários de início (ex: "03:00:00").
    end_times : list of str
        Lista contendo os horários de fim (ex: "03:15:00").
    day : str
        A data base para os eventos (ex: "2012-11-29").
    file_path : str, optional
        Caminho para o ficheiro JSON de destino.
        O padrão é "temp/events.json".

    Returns
    -------
    None

    Examples
    --------
    >>> starts = ["03:00:00", "03:45:00"]
    >>> ends = ["03:15:00", "04:00:00"]
    >>> save_event_times_to_json(starts, ends, "2012-11-29")
    # Conteúdo do JSON:
    # [
    #   {"start": "2012-11-29 03:00:00", "end": "2012-11-29 03:15:00"},
    #   {"start": "2012-11-29 03:45:00", "end": "2012-11-29 04:00:00"}
    # ]
    """
    # Criamos a string completa combinando a data com o horário
    # O .strip() garante que não fiquem espaços sobrando se a entrada vier suja
    events_list = [
        {
            "start": f"{day.strip()} {start.strip()}", 
            "end": f"{day.strip()} {end.strip()}"
        } 
        for start, end in zip(start_times, end_times)
    ]
    
    target_path = pathlib.Path(file_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(events_list, f, indent=4, ensure_ascii=False)


def load_event_times_from_json(file_path: str = "temp/events.json") -> list:
    """
    Lê o ficheiro JSON e converte as strings de tempo em objetos datetime.

    Parameters
    ----------
    file_path : str, optional
        Caminho do ficheiro JSON a ser lido.
        O padrão é "temp/events.json".

    Returns
    -------
    list of dict
        Uma lista de dicionários onde as chaves 'start' e 'end' contêm 
        objetos datetime. Retorna uma lista vazia se o ficheiro não existir.

    Examples
    --------
    >>> events = load_event_times_from_json()
    >>> type(events[0]['start'])
    <class 'datetime.datetime'>
    """
    path = pathlib.Path(file_path)
    
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        raw_events = json.load(f)

    # Converte as strings de volta para objetos datetime
    formatted_events = []
    for ev in raw_events:
        formatted_events.append({
            "start": datetime.strptime(ev["start"], "%Y-%m-%d %H:%M:%S"),
            "end": datetime.strptime(ev["end"], "%Y-%m-%d %H:%M:%S")
        })

    return formatted_events