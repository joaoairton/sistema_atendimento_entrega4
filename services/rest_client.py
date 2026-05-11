# services/rest_client.py
# Cliente REST — chamadas que o Atendimento faz PARA outros sistemas.
# Toda comunicação de saída passa por aqui.

import time, requests, json
import config


def _chamar(metodo, url, payload=None, sistema=None):
    """
    Retorna (sucesso, dados, http_status, erro).
    """
    inicio      = time.time()
    payload_str = json.dumps(payload, ensure_ascii=False) if payload else None

    try:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        if metodo == "GET":
            resp = requests.get(url,  timeout=config.REST_TIMEOUT, headers=headers)
        elif metodo == "POST":
            resp = requests.post(url, json=payload, timeout=config.REST_TIMEOUT, headers=headers)
        elif metodo == "PUT":
            resp = requests.put(url,  json=payload, timeout=config.REST_TIMEOUT, headers=headers)
        else:
            raise ValueError(f"Método não suportado: {metodo}")

        duracao = int((time.time() - inicio) * 1000)
        sucesso = resp.status_code in (200, 201)

        try:
            dados = resp.json()
        except Exception:
            dados = {}

        return sucesso, dados, resp.status_code, None

    except requests.exceptions.Timeout:
        duracao = int((time.time() - inicio) * 1000)
        erro    = f"Timeout apos {config.REST_TIMEOUT}s"
        return False, {}, None, erro

    except requests.exceptions.ConnectionError:
        duracao = int((time.time() - inicio) * 1000)
        erro    = f"Sistema indisponivel: {url}"
        return False, {}, None, erro

    except Exception as e:
        duracao = int((time.time() - inicio) * 1000)
        return False, {}, None, str(e)


# Chamadas ao Estoque

def enviar_prescricao(prescricao: dict):
    """POST /api/prescricoes — envia prescrição, recebe status do medicamento."""
    url = f"{config.ESTOQUE_BASE_URL}/api/prescricoes"
    payload = {
        "id_prescricao":      prescricao["id"],
        "cpf_paciente":       prescricao["cpf_paciente"],
        "codigo_medicamento": prescricao["codigo_med"],
        "quantidade":         float(prescricao["quantidade"]),
        "unidade":            prescricao["unidade"].strip()
    }
    return _chamar("POST", url, payload, sistema="ESTOQUE")


def reservar_medicamento(id_prescricao: int, codigo_med: int, quantidade: float):
    """PUT /api/prescricoes/<id>/reservar — confirma reserva."""
    url = f"{config.ESTOQUE_BASE_URL}/api/prescricoes/{id_prescricao}/reservar"
    payload = {"codigo_medicamento": codigo_med, "quantidade": quantidade}
    return _chamar("PUT", url, payload, sistema="ESTOQUE")


# Chamadas ao Financeiro

def consultar_status_financeiro(cpf: str):
    """GET /api/pacientes/<cpf>/status-financeiro — status em tempo real."""
    url = f"{config.FINANCEIRO_BASE_URL}/api/pacientes/{cpf}/status-financeiro"
    return _chamar("GET", url, sistema="FINANCEIRO")


def enviar_finalizacao(atendimento: dict, prescricoes: list):
    """POST /api/atendimentos — envia finalização para faturamento."""
    url = f"{config.FINANCEIRO_BASE_URL}/api/atendimentos"
    payload = {
        "id_atendimento":   atendimento["id"],
        "cpf_paciente":     atendimento["cpf_paciente"],
        "data_atendimento": str(atendimento["data_finalizacao"]),
        "tipo_atendimento": atendimento["tipo"],
        "cid":              atendimento["cid"] or "",
        "codigo_tuss":      atendimento["codigo_tuss"] or "",
        "convenio":         atendimento["convenio"] or "PARTICULAR",
        "carteirinha":      atendimento["carteirinha"] or "",
        "qtd_medicamentos": len(prescricoes),
        "valor_total":      float(atendimento["valor_total"] or 0)
    }
    return _chamar("POST", url, payload, sistema="FINANCEIRO")
