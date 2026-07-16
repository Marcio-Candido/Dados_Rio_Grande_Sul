import pandas as pd
import numpy as np
import requests

# Gerar um dataframe com os resultados das estações
def acharar_estacao(registro: dict) -> dict:
    r = registro
    
    def val(container, *chaves):
        obj = container
        for chave in chaves:
            if isinstance(obj, dict):
                obj = obj.get(chave, {})
            else:
                return None
        return obj.get('value') if isinstance(obj, dict) else None
    
    return {
        'codigo': r.get('codigo'),
        'estacao': r.get('name', {}).get('general'),
        'timestamp': r.get('timestamp'),
        'bacia': r.get('position', {}).get('bacia'),
        'latitude': r.get('position', {}).get('latitude'),
        'longitude': r.get('position', {}).get('longitude'),
        'regiao': r.get('position', {}).get('regiao'),
        'altitude': r.get('position', {}).get('altitude'),
        'chuva_1h_mm': val(r, 'data', 'chuva', 'acumulado', 'h001'),
        'chuva_6h_mm': val(r, 'data', 'chuva', 'acumulado', 'h006'),
        'chuva_12h_mm': val(r, 'data', 'chuva', 'acumulado', 'h012'),
        'chuva_24h_mm': val(r, 'data', 'chuva', 'acumulado', 'h024'),
        'chuva_48h_mm': val(r, 'data', 'chuva', 'acumulado', 'h048'),
        'rio_nivel_m': val(r, 'data', 'rio', 'rio_nivel'),
        'rio_tendencia': val(r, 'data', 'rio', 'rio_nivel_tendencia'),
     }

# Fazer a consulta a base de dados
def consulta_dados(codigos:str) -> dict:
    ENDPOINT = "https://redehidrometeorologica.defesacivil.rs.gov.br/graphql"
    query = f"""{{
        tags_data(
            station: [{codigos}]
            clients: ["casa-militar-defesa-civil-rs"]
            filters: {{
                localizacao: [{{
                    codigos: ["43"]
                    tipo: UNIDADE_FEDERATIVA
                }}]
            }}
        ) {{
            qualle_meteorologia {{
                codigo
                name {{ prefix general local }}
                timestamp
                position {{ bacia latitude longitude regiao altitude }}
                data {{
                    chuva {{
                        acumulado {{
                            h001 {{ value }}
                            h006 {{ value }}
                            h012 {{ value }}
                            h024 {{ value }}
                            h048 {{ value }}
                        }} }}
                     rio {{
                        rio_nivel {{ value }}
                        rio_nivel_tendencia {{ value }}
                        }}
                }}
                 
            }}
        }}
    }}"""
    resp = requests.post(ENDPOINT, json={"query": query}, timeout=30)
    return dict(resp.json())
if __name__=='__main__':
    # Baixar os dados
    codigos = ','.join([f'"DCRS-{str(a):>05s}"' for a in np.arange(1,131)])
    dados = consulta_dados(codigos)
    lista_estacoes = dados['data']['tags_data']['qualle_meteorologia']
    linhas = [acharar_estacao(est) for est in lista_estacoes]
    df = pd.DataFrame(linhas) 
    colunas = ['codigo', 'estacao', 'timestamp','latitude', 'longitude','chuva_1h_mm', 'chuva_6h_mm', 'chuva_12h_mm',
           'chuva_24h_mm', 'chuva_48h_mm', 'rio_nivel_m', 'rio_tendencia']

    # Salvar dados
    arq = 'dados/dados_DCRS.txt'
    df.to_csv(arq, index=False, mode='a', header=False)