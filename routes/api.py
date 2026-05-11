# routes/api.py
# Endpoints REST que o sistema de Atendimento EXPOE para outros sistemas.
# Estes são os endpoints que o Financeiro e o Estoque vão chamar.

from flask import Blueprint, request, jsonify
from services import db_service as db

api_bp = Blueprint("api", __name__, url_prefix="/api")



# Pacientes

@api_bp.route("/pacientes", methods=["GET"])
def listar_pacientes():
    """
    GET /api/pacientes
    Lista todos os pacientes cadastrados.
    Outros sistemas podem consultar para verificar se o paciente existe.
    """
    pacientes = db.listar_pacientes()
    dados = [{"cpf": p["cpf"], "nome": p["nome"],
              "data_nasc": str(p["data_nasc"]) if p["data_nasc"] else None,
              "telefone": p["telefone"], "email": p["email"]}
             for p in pacientes]
    return jsonify({"pacientes": dados, "total": len(dados)}), 200


@api_bp.route("/pacientes/<cpf>", methods=["GET"])
def buscar_paciente(cpf):
    """
    GET /api/pacientes/<cpf>
    Retorna dados do paciente pelo CPF.
    """
    pac = db.buscar_paciente(cpf)
    if not pac:
        return jsonify({"erro": "Paciente nao encontrado"}), 404

    return jsonify({
        "cpf":       pac["cpf"],
        "nome":      pac["nome"],
        "data_nasc": str(pac["data_nasc"]) if pac["data_nasc"] else None,
        "telefone":  pac["telefone"],
        "email":     pac["email"]
    }), 200


@api_bp.route("/pacientes/<cpf>/status-financeiro", methods=["GET"])
def status_financeiro(cpf):
    """
    GET /api/pacientes/<cpf>/status-financeiro
    Retorna o status financeiro mais recente do paciente.
    Consultado pelo Financeiro para verificar elegibilidade.
    """
    sf = db.buscar_status_financeiro(cpf)
    if not sf:
        return jsonify({"erro": "Status financeiro nao disponivel para este CPF"}), 404

    return jsonify({
        "cpf_paciente":        sf["cpf_paciente"],
        "status_financeiro":   sf["status_financeiro"],
        "permite_atendimento": sf["permite_atendimento"],
        "qtd_pendencias":      sf["qtd_pendencias"],
        "valor_total_pendente": float(sf["valor_total_pendente"]),
        "observacao":          sf["observacao"],
        "consultado_em":       sf["consultado_em"].isoformat()
    }), 200


# Atendimentos

@api_bp.route("/atendimentos", methods=["GET"])
def listar_atendimentos():
    """
    GET /api/atendimentos
    Lista atendimentos. Outros sistemas podem consultar para rastreabilidade.
    """
    atendimentos = db.listar_atendimentos()
    dados = [{"id": a["id"], "cpf_paciente": a["cpf_paciente"],
              "nome_paciente": a["nome_paciente"],
              "tipo": a["tipo"], "status": a["status"],
              "data_abertura": str(a["data_abertura"])}
             for a in atendimentos]
    return jsonify({"atendimentos": dados, "total": len(dados)}), 200


@api_bp.route("/atendimentos/<int:id_atend>", methods=["GET"])
def buscar_atendimento(id_atend):
    """
    GET /api/atendimentos/<id>
    Retorna dados completos de um atendimento.
    """
    atend = db.buscar_atendimento(id_atend)
    if not atend:
        return jsonify({"erro": "Atendimento nao encontrado"}), 404

    return jsonify({
        "id":             atend["id"],
        "cpf_paciente":   atend["cpf_paciente"],
        "nome_paciente":  atend["nome_paciente"],
        "tipo":           atend["tipo"],
        "status":         atend["status"],
        "crm_medico":     atend["crm_medico"],
        "convenio":       atend["convenio"],
        "data_abertura":  str(atend["data_abertura"]),
        "hora_abertura":  str(atend["hora_abertura"]),
        "cid":            atend["cid"],
        "codigo_tuss":    atend["codigo_tuss"],
        "valor_total":    float(atend["valor_total"]) if atend["valor_total"] else None,
        "data_finalizacao": str(atend["data_finalizacao"]) if atend["data_finalizacao"] else None
    }), 200


# Prescricoes

@api_bp.route("/atendimentos/<int:id_atend>/prescricoes", methods=["GET"])
def listar_prescricoes(id_atend):
    """
    GET /api/atendimentos/<id>/prescricoes
    Lista prescrições de um atendimento com status do Estoque.
    """
    atend = db.buscar_atendimento(id_atend)
    if not atend:
        return jsonify({"erro": "Atendimento nao encontrado"}), 404

    prescricoes = db.buscar_prescricoes_atendimento(id_atend)
    dados = [{
        "id":             p["id"],
        "codigo_med":     p["codigo_med"],
        "quantidade":     float(p["quantidade"]),
        "unidade":        p["unidade"].strip(),
        "status_estoque": p["status_estoque"],
        "obs_estoque":    p["obs_estoque"],
        "data_prescricao": str(p["data_prescricao"])
    } for p in prescricoes]

    return jsonify({"id_atendimento": id_atend, "prescricoes": dados,
                    "total": len(dados)}), 200
