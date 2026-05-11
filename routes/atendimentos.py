# routes/atendimentos.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from services import db_service as db
from services import rest_client as rest

atend_bp = Blueprint("atendimentos", __name__)


@atend_bp.route("/atendimentos")
def listar():
    return render_template("atendimentos/listar.html",
                           atendimentos=db.listar_atendimentos())


@atend_bp.route("/atendimentos/novo", methods=["GET","POST"])
def novo():
    if request.method == "POST":
        cpf  = request.form.get("cpf","").replace(".","").replace("-","")
        tipo = request.form.get("tipo")
        if not db.buscar_paciente(cpf):
            flash(("erro","Paciente nao encontrado. Cadastre-o primeiro."))
            return render_template("atendimentos/novo.html")

        # Consulta status financeiro em tempo real via REST
        sucesso, dados_fin, _, erro_fin = rest.consultar_status_financeiro(cpf)

        if sucesso:
            permite = dados_fin.get("permite_atendimento","S")
            db.salvar_status_financeiro(
                cpf=cpf,
                status_fin=dados_fin.get("status_financeiro","REGULAR"),
                qtd_pendencias=dados_fin.get("qtd_pendencias",0),
                valor_pendente=dados_fin.get("valor_total_pendente",0),
                data_vencimento=None,
                permite_atendimento=permite,
                observacao=dados_fin.get("observacao")
            )
            if permite == "N":
                flash(("erro",
                    f"Atendimento bloqueado. Status: {dados_fin.get('status_financeiro')}. "
                    f"Pendencias: {dados_fin.get('qtd_pendencias')} "
                    f"(R$ {dados_fin.get('valor_total_pendente',0):.2f})."))
                return render_template("atendimentos/novo.html")
            if permite == "E" and tipo != "EMERGENCIA":
                flash(("erro",
                    f"Paciente com restricao financeira. "
                    f"Apenas EMERGENCIA permitida. Tipo selecionado: {tipo}."))
                return render_template("atendimentos/novo.html")
            
        else:
            # Financeiro offline — usa ultimo status local
            sf = db.buscar_status_financeiro(cpf)
            if sf:
                flash(("aviso",
                    f"Sistema Financeiro indisponivel. "
                    f"Usando ultimo status local: {sf['status_financeiro']} "
                    f"(consultado em {sf['consultado_em'].strftime('%d/%m/%Y %H:%M')})."))

                # Aplica as mesmas regras do status online
                permite = sf["permite_atendimento"]
                if permite == "N":
                    flash(("erro",
                        f"Atendimento bloqueado. Status financeiro local: "
                        f"{sf['status_financeiro']}. "
                        f"Pendencias: {sf['qtd_pendencias']} "
                        f"(R$ {sf['valor_total_pendente']:.2f})."))
                    return render_template("atendimentos/novo.html")

                if permite == "E" and tipo != "EMERGENCIA":
                    flash(("erro",
                        f"Paciente com restricao financeira. "
                        f"Somente EMERGENCIA permitida. "
                        f"Tipo selecionado: {tipo}."))
                    return render_template("atendimentos/novo.html")
            else:
                flash(("aviso", "Sistema Financeiro indisponivel e sem status local. "
                    "Prosseguindo sem verificacao financeira."))

        id_atend = db.abrir_atendimento(
            cpf=cpf, tipo=tipo,
            crm=request.form.get("crm") or None,
            convenio=request.form.get("convenio") or None,
            carteirinha=request.form.get("carteirinha") or None,
        )
        flash(("ok", f"Atendimento #{id_atend} aberto."))
        return redirect(url_for("atendimentos.detalhe", id=id_atend))
    return render_template("atendimentos/novo.html")


@atend_bp.route("/atendimentos/<int:id>")
def detalhe(id):
    atend = db.buscar_atendimento(id)
    if not atend:
        flash(("erro","Atendimento nao encontrado."))
        return redirect(url_for("atendimentos.listar"))
    prescricoes      = db.buscar_prescricoes_atendimento(id)
    sem_retorno      = db.prescricoes_sem_retorno(id) if atend["status"]=="ABERTO" else []
    return render_template("atendimentos/detalhe.html",
                           atend=atend, prescricoes=prescricoes,
                           sem_retorno=sem_retorno)


@atend_bp.route("/atendimentos/<int:id>/finalizar", methods=["GET","POST"])
def finalizar(id):
    atend = db.buscar_atendimento(id)
    if not atend or atend["status"] != "ABERTO":
        flash(("erro","Atendimento nao encontrado ou ja finalizado."))
        return redirect(url_for("atendimentos.listar"))

    sem_retorno = db.prescricoes_sem_retorno(id)
    if sem_retorno:
        codigos = ", ".join(str(p["codigo_med"]) for p in sem_retorno)
        flash(("erro",
            f"Nao e possivel finalizar: {len(sem_retorno)} prescricao(oes) "
            f"sem retorno do Estoque (cod: {codigos})."))
        return redirect(url_for("atendimentos.detalhe", id=id))

    prescricoes = db.buscar_prescricoes_atendimento(id)

    if request.method == "POST":
        cid         = request.form.get("cid","").strip().upper()
        codigo_tuss = request.form.get("codigo_tuss","").strip()
        valor       = float(request.form.get("valor_total","0").replace(",",".") or 0)
        obs         = request.form.get("observacoes","").strip() or None

        if not db.finalizar_atendimento(id, cid, codigo_tuss, valor, obs):
            flash(("erro","Falha ao finalizar atendimento."))
            return redirect(url_for("atendimentos.detalhe", id=id))

        atend = db.buscar_atendimento(id)

        # Envia finalização ao Financeiro via REST
        sucesso, _, status_http, erro = rest.enviar_finalizacao(
            dict(atend), [dict(p) for p in prescricoes])

        if sucesso:
            flash(("ok", f"Atendimento #{id} finalizado e enviado ao Financeiro."))
        else:
            flash(("aviso",
                f"Atendimento finalizado localmente. "
                f"Falha ao enviar ao Financeiro: {erro or f'HTTP {status_http}'}. "
                f"Reenvio necessario."))

        return redirect(url_for("atendimentos.detalhe", id=id))

    return render_template("atendimentos/finalizar.html",
                           atend=atend, prescricoes=prescricoes)
