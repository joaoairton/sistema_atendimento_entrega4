# routes/pacientes.py
import psycopg2
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from services import db_service as db
from services import rest_client as rest

pac_bp = Blueprint("pacientes", __name__)


@pac_bp.route("/pacientes")
def listar():
    return render_template("pacientes/listar.html", pacientes=db.listar_pacientes())


@pac_bp.route("/pacientes/novo", methods=["GET", "POST"])
def novo():
    if request.method == "POST":
        cpf  = request.form.get("cpf","").replace(".","").replace("-","")
        nome = request.form.get("nome","").strip()
        if len(cpf)!=11 or not cpf.isdigit():
            flash(("erro","CPF invalido."))
            return render_template("pacientes/novo.html")
        if not nome:
            flash(("erro","Nome e obrigatorio."))
            return render_template("pacientes/novo.html")
        try:
            db.cadastrar_paciente(cpf, nome,
                request.form.get("data_nasc") or None,
                request.form.get("telefone") or None,
                request.form.get("email") or None)
            flash(("ok", f"Paciente {nome.upper()} cadastrado."))
            return redirect(url_for("pacientes.listar"))
        except psycopg2.errors.UniqueViolation:
            flash(("erro","CPF ja cadastrado."))
    return render_template("pacientes/novo.html")

# Editar um cadastro de paciente
@pac_bp.route("/pacientes/<cpf>/editar", methods=["GET", "POST"])
def editar(cpf):
    pac = db.buscar_paciente(cpf)
    if not pac:
        flash(("erro", "Paciente não encontrado."))
        return redirect(url_for("pacientes.listar"))

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        if not nome:
            flash(("erro", "Nome é obrigatório."))
            return render_template("pacientes/editar.html", pac=pac)

        db.atualizar_paciente(
            cpf,
            nome,
            request.form.get("data_nasc") or None,
            request.form.get("telefone") or None,
            request.form.get("email") or None,
        )
        flash(("ok", f"Paciente {nome.upper()} atualizado."))
        return redirect(url_for("pacientes.listar"))

    return render_template("pacientes/editar.html", pac=pac)


@pac_bp.route("/api/paciente-local/<cpf>")
def api_buscar_local(cpf):
    """API interna usada pelo JS — retorna dados do paciente E status financeiro."""
    cpf = cpf.replace(".","").replace("-","")
    pac = db.buscar_paciente(cpf)
    if not pac:
        return jsonify({"encontrado": False})

    # Tenta buscar status financeiro no Financeiro via REST em tempo real
    sucesso, dados_fin, _, erro = rest.consultar_status_financeiro(cpf)

    if sucesso:
        # Grava localmente para referência futura
        db.salvar_status_financeiro(
            cpf=cpf,
            status_fin=dados_fin.get("status_financeiro","NAO_VERIFICADO"),
            qtd_pendencias=dados_fin.get("qtd_pendencias",0),
            valor_pendente=dados_fin.get("valor_total_pendente",0),
            data_vencimento=None,
            permite_atendimento=dados_fin.get("permite_atendimento","S"),
            observacao=dados_fin.get("observacao")
        )
        status_fin = dados_fin.get("status_financeiro","NAO_VERIFICADO")
        permite    = dados_fin.get("permite_atendimento","S")
    else:
        # Financeiro indisponivel — usa ultimo status local se existir
        sf = db.buscar_status_financeiro(cpf)
        status_fin = sf["status_financeiro"] if sf else "NAO_VERIFICADO"
        permite    = sf["permite_atendimento"] if sf else "S"

    return jsonify({
        "encontrado":        True,
        "nome":              pac["nome"],
        "status_financeiro": status_fin,
        "permite_atendimento": permite,
        "financeiro_online": sucesso
    })
