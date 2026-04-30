import json
import pathlib
import hashlib
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.config import Base, DB_PATH, EVENTS_DATA_DIR
from src.database.models import Day, InputConfig, EventMetadata

def save_event_times_to_db(data_to_save: dict) -> None:
    """
    Salva metadados de eventos no SQLite e dados numéricos em arquivos JSON.

    Esta função implementa uma abordagem de armazenamento híbrido. Os metadados
    dos eventos e as configurações de entrada são normalizados em um banco de
    dados SQLite utilizando SQLAlchemy com identificadores únicos (UUID). 
    Os dados numéricos de alta densidade (séries temporais x, y e índices de 
    curvas) são extraídos e armazenados em arquivos JSON individuais no sistema 
     de arquivos, organizados por uma estrutura de diretórios cronológica.

    A função também realiza a de-duplicação de configurações: se um conjunto
    de parâmetros de entrada para um determinado dia já existir no banco, 
    os novos eventos serão vinculados à configuração existente em vez de 
    criar uma duplicata.

    Parameters
    ----------
    data_to_save : dict
        Dicionário aninhado onde as chaves são strings de datas (ISO 8601) 
        e os valores são dicionários contendo:
        
        - 'input_data' : dict
            Parâmetros de configuração (data_select, smooth_window, etc.).

        - 'event_data' : list of dict;

            Lista de eventos, onde cada item contém:
                - 'metadata' : dict (start_time, end_time, is_valid, etc.).
                - 'numeric_data' : dict (x, y, curves).

    Returns
    -------
    None

    Raises
    ------
    Exception
        Se houver falha na conexão com o banco de dados, falha na escrita 
        dos arquivos JSON ou erro de integridade referencial, a transação 
        sofre rollback e a exceção é relançada.

    Notes
    -----
    A estrutura de diretórios para os arquivos JSON segue o padrão:
    `database/events/YYYY/MM/DD/event_<uuid>.json`.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVENTS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    engine = create_engine(f"sqlite:///{DB_PATH}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        for day_str, content in data_to_save.items():
            # 1. Obter ou criar o Dia
            day_entry = session.query(Day).filter_by(date_str=day_str).first()
            if not day_entry:
                day_entry = Day(date_str=day_str)
                session.add(day_entry)
                session.flush()

            # 2. Gerar Hash Único dos inputs
            inputs = content['input_data']
            # O sort_keys é CRITICAL para o hash ser sempre o mesmo para os mesmos valores
            hash_str = json.dumps(inputs, sort_keys=True)
            config_hash = hashlib.md5(hash_str.encode()).hexdigest()

            # 3. Detectar se essa exata config já existe para este dia
            config_entry = session.query(InputConfig).filter_by(
                day_id=day_entry.id, 
                config_hash=config_hash
            ).first()

            if not config_entry:
                # Cria nova configuração se não encontrar o hash
                config_entry = InputConfig(
                    day_id=day_entry.id, 
                    config_hash=config_hash,
                    **inputs # Desempacota o dicionário direto nas colunas da tabela
                )
                session.add(config_entry)
                session.flush()

            # 4. Salvar Eventos vinculados à config (existente ou nova)
            for event in content['event_data']:
                meta = event['metadata']
                numeric = event['numeric_data']

                new_event = EventMetadata(
                    config_id=config_entry.id,
                    start_time=f"{day_str} {meta['start_time']}",
                    end_time=f"{day_str} {meta['end_time']}",
                    curve_select=meta['curve_select'],
                    offset=meta['offset'],
                    is_automatic=meta['is_automatic'],
                    is_edited=meta['is_edited'],
                    is_valid=meta['is_valid']
                )
                session.add(new_event)
                session.flush() 

                # 5. Salvar JSON Híbrido
                date_dt = datetime.strptime(day_str, "%Y-%m-%d")
                rel_path = pathlib.Path(f"{date_dt.year}/{date_dt.month:02d}/{date_dt.day:02d}")
                full_path = EVENTS_DATA_DIR / rel_path
                full_path.mkdir(parents=True, exist_ok=True)

                filename = f"event_{new_event.id}.json"
                with open(full_path / filename, "w", encoding="utf-8") as f:
                    json.dump(numeric, f, indent=4)

                new_event.numeric_data_path = str(rel_path / filename)

        session.commit()
        print("Log processado com sucesso.")

    except Exception as e:
        session.rollback()
        print(f"Erro na transação: {e}")
        raise
    finally:
        session.close()


def load_event_from_db(date_str: str) -> dict:
    """
    Recupera todos os logs e dados numéricos de um dia específico do banco de dados.

    Realiza uma consulta ao banco de dados SQLite para encontrar todas as 
    configurações e metadados de eventos associados à data fornecida. Para cada 
    evento encontrado, o arquivo JSON correspondente é lido do sistema de 
    arquivos para reconstruir o dicionário completo de dados.

    Parameters
    ----------
    date_str : str
        A data base para consulta no formato "YYYY-MM-DD" (ex: "2012-11-29").

    Returns
    -------
    dict
        Dicionário formatado com as chaves 'input_data' e 'event_data', 
        seguindo a estrutura original de salvamento. Retorna um dicionário 
        vazio caso a data não possua registros.

    Notes
    -----
    A função pressupõe que os arquivos JSON estão acessíveis no caminho 
    relativo armazenado na coluna `numeric_data_path` a partir do 
    diretório `database/events/`.

    Examples
    --------
    >>> data = load_events_from_db("2012-11-29")
    >>> print(data.keys())
    dict_keys(['input_data', 'event_data'])
    """
    engine = create_engine(f"sqlite:///{DB_PATH}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Buscar o dia e as configurações associadas
        day_entry = session.query(Day).filter_by(date_str=date_str).first()
        
        if not day_entry:
            return {}

        # Pegamos a última configuração usada para esse dia (ou você pode filtrar)
        # Aqui, como exemplo, vamos pegar a configuração mais recente
        config_entry = session.query(InputConfig).filter_by(day_id=day_entry.id).last()

        if not config_entry:
            return {}

        # 2. Reconstruir o dicionário de inputs (pegando as colunas da tabela)
        input_data = {
            "data_select": config_entry.data_select,
            "interpolation_select": config_entry.interpolation_select,
            "smooth_window": config_entry.smooth_window,
            "n_apply_smooth": config_entry.n_apply_smooth,
            "diff_std": config_entry.diff_std,
            "number_of_segments": config_entry.number_of_segments,
            "quantity_mean_std": config_entry.quantity_mean_std,
            "merge_gap": config_entry.merge_gap,
            "relative_height": config_entry.relative_height,
            "avoid_border": config_entry.avoid_border,
            "min_curves": config_entry.min_curves,
            "dtw_weight": config_entry.dtw_weight
        }

        # 3. Buscar os eventos vinculados a essa config
        events_list = []
        for ev in config_entry.events:
            # Carregar o dado numérico do arquivo JSON
            json_full_path = EVENTS_DATA_DIR / ev.numeric_data_path
            
            numeric_data = {}
            if json_full_path.exists():
                with open(json_full_path, "r", encoding="utf-8") as f:
                    numeric_data = json.load(f)

            # Montar o objeto de metadata (removendo a data do timestamp se necessário)
            # aqui estamos pegando como salvo: "YYYY-MM-DD HH:MM:SS"
            events_list.append({
                "metadata": {
                    "start_time": ev.start_time.split(" ")[1], # Pega só o HH:MM:SS
                    "end_time": ev.end_time.split(" ")[1],
                    "curve_select": ev.curve_select,
                    "offset": ev.offset,
                    "is_automatic": ev.is_automatic,
                    "is_edited": ev.is_edited,
                    "is_valid": ev.is_valid
                },
                "numeric_data": numeric_data
            })

        return {
            "input_data": input_data,
            "event_data": events_list
        }

    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        return {}
    finally:
        session.close()