# routes/prescricoes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from services import db_service as db
from services import rest_client as rest

pres_bp = Blueprint("prescricoes", __name__)


@pres_bp.route("/atendimentos/<int:id_atend>/prescricao", methods=["GET","POST"])
def nova(id_atend):
    atend = db.buscar_atendimento(id_atend)
    if not atend or atend["status"] != "ABERTO":
        flash(("erro","Atendimento nao encontrado ou ja finalizado."))
        return redirect(url_for("atendimentos.listar"))

    prescricoes = db.buscar_prescricoes_atendimento(id_atend)

    if request.method == "POST":
        try:
            codigo_med = int(request.form.get("codigo_med",0))
            quantidade = float(request.form.get("quantidade","0").replace(",","."))
            unidade    = request.form.get("unidade","COMP")
            crm        = request.form.get("crm","").strip() or atend["crm_medico"] or ""
            instrucoes = request.form.get("instrucoes","").strip() or None

            # 1. Grava no banco
            id_pres, _, _ = db.registrar_prescricao(
                id_atend, atend["cpf_paciente"], crm,
                codigo_med, quantidade, unidade, instrucoes)

            prescricao = db.buscar_prescricao(id_pres)

            # 2. Envia ao Estoque via REST — resposta em tempo real
            sucesso, dados, status_http, erro = rest.enviar_prescricao(dict(prescricao))

            if sucesso:
                status_est   = dados.get("status","DESCONHECIDO")
                obs_est      = dados.get("observacao","")

                # 3. Grava retorno do Estoque
                db.salvar_retorno_estoque(id_pres, codigo_med, status_est, obs_est)

                if status_est in ("DISPONIVEL","SEPARADO"):
                    flash(("ok",
                        f"Prescricao #{id_pres} registrada. "
                        f"Estoque: {status_est}. {obs_est}"))
                else:
                    flash(("aviso",
                        f"Prescricao #{id_pres} registrada. "
                        f"Estoque: {status_est}. {obs_est}"))
            else:
                flash(("aviso",
                    f"Prescricao #{id_pres} registrada localmente. "
                    f"Estoque nao respondeu: {erro or f'HTTP {status_http}'}. "
                    f"Retentativa necessaria."))

        except Exception as e:
            flash(("erro", f"Erro ao registrar prescricao: {e}"))

        return redirect(url_for("prescricoes.nova", id_atend=id_atend))

    return render_template("prescricoes/nova.html",
                           atend=atend, prescricoes=prescricoes)


@pres_bp.route("/prescricoes/<int:id_pres>/reenviar", methods=["POST"])
def reenviar(id_pres):
    """Retenta envio ao Estoque para prescrições sem retorno."""
    pres = db.buscar_prescricao(id_pres)
    if not pres:
        flash(("erro","Prescricao nao encontrada."))
        return redirect(url_for("atendimentos.listar"))

    sucesso, dados, status_http, erro = rest.enviar_prescricao(dict(pres))

    if sucesso:
        db.salvar_retorno_estoque(id_pres, pres["codigo_med"],
                                  dados.get("status","DESCONHECIDO"),
                                  dados.get("observacao",""))
        flash(("ok", f"Retentativa bem-sucedida. Estoque: {dados.get('status')}."))
    else:
        flash(("erro", f"Estoque ainda indisponivel: {erro or f'HTTP {status_http}'}."))

    return redirect(url_for("atendimentos.detalhe", id=pres["id_atendimento"]))
