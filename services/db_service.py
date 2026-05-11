# services/db_service.py — Entrega 4
from config import get_db, get_cur


# Paciente

def buscar_paciente(cpf):
    db=get_db(); cur=get_cur(db)
    try:
        cur.execute("SELECT * FROM paciente WHERE cpf=%s",(cpf,))
        return cur.fetchone()
    finally:
        cur.close(); db.close()

def cadastrar_paciente(cpf,nome,data_nasc=None,telefone=None,email=None):
    db=get_db(); cur=db.cursor()
    try:
        cur.execute("INSERT INTO paciente(cpf,nome,data_nasc,telefone,email) VALUES(%s,%s,%s,%s,%s)",
            (cpf,nome.upper(),data_nasc or None,telefone or None,email or None))
        db.commit()
    finally:
        cur.close(); db.close()

def listar_pacientes():
    db=get_db(); cur=get_cur(db)
    try:
        cur.execute("SELECT * FROM paciente ORDER BY nome")
        return cur.fetchall()
    finally:
        cur.close(); db.close()

def atualizar_paciente(cpf, nome, data_nasc=None, telefone=None, email=None):
    db = get_db(); cur = db.cursor()
    try:
        cur.execute("""
            UPDATE paciente SET
                nome      = %s,
                data_nasc = %s,
                telefone  = %s,
                email     = %s
            WHERE cpf = %s
        """, (nome.upper(), data_nasc or None,
              telefone or None, email or None, cpf))
        db.commit()
    finally:
        cur.close(); db.close()


# Atendimento

def abrir_atendimento(cpf,tipo,crm=None,convenio=None,carteirinha=None):
    db=get_db(); cur=db.cursor()
    try:
        cur.execute("""INSERT INTO atendimento(cpf_paciente,tipo,crm_medico,convenio,carteirinha)
            VALUES(%s,%s,%s,%s,%s) RETURNING id""",
            (cpf,tipo,crm or None,convenio or None,carteirinha or None))
        id_atend=cur.fetchone()[0]; db.commit(); return id_atend
    finally:
        cur.close(); db.close()

def buscar_atendimento(id_atend):
    db=get_db(); cur=get_cur(db)
    try:
        cur.execute("""SELECT a.*,p.nome AS nome_paciente FROM atendimento a
            JOIN paciente p ON p.cpf=a.cpf_paciente WHERE a.id=%s""",(id_atend,))
        return cur.fetchone()
    finally:
        cur.close(); db.close()

def listar_atendimentos():
    db=get_db(); cur=get_cur(db)
    try:
        cur.execute("""SELECT a.id,a.tipo,a.status,a.data_abertura,
            p.nome AS nome_paciente,a.cpf_paciente
            FROM atendimento a JOIN paciente p ON p.cpf=a.cpf_paciente
            ORDER BY a.data_abertura DESC,a.hora_abertura DESC""")
        return cur.fetchall()
    finally:
        cur.close(); db.close()

def finalizar_atendimento(id_atend,cid,codigo_tuss,valor_total,observacoes=None):
    db=get_db(); cur=db.cursor()
    try:
        cur.execute("""UPDATE atendimento SET status='FINALIZADO',cid=%s,
            codigo_tuss=%s,valor_total=%s,data_finalizacao=CURRENT_DATE,
            hora_finalizacao=CURRENT_TIME,observacoes=%s
            WHERE id=%s AND status='ABERTO'
            RETURNING id,data_finalizacao,hora_finalizacao""",
            (cid,codigo_tuss,valor_total,observacoes or None,id_atend))
        row=cur.fetchone(); db.commit(); return row
    finally:
        cur.close(); db.close()


# Prescricao

def registrar_prescricao(id_atend,cpf,crm,codigo_med,quantidade,unidade,instrucoes=None):
    db=get_db(); cur=db.cursor()
    try:
        unidade_fmt=unidade.strip().upper().ljust(4)[:4]
        cur.execute("""INSERT INTO prescricao(id_atendimento,cpf_paciente,crm_medico,
            codigo_med,quantidade,unidade,instrucoes)
            VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id,data_prescricao,hora_prescricao""",
            (id_atend,cpf,crm or None,codigo_med,quantidade,unidade_fmt,instrucoes or None))
        row=cur.fetchone(); db.commit(); return row[0],row[1],row[2]
    finally:
        cur.close(); db.close()

def buscar_prescricao(id_pres):
    db=get_db(); cur=get_cur(db)
    try:
        cur.execute("SELECT * FROM prescricao WHERE id=%s",(id_pres,))
        return cur.fetchone()
    finally:
        cur.close(); db.close()

def buscar_prescricoes_atendimento(id_atend):
    db=get_db(); cur=get_cur(db)
    try:
        cur.execute("""SELECT p.*,re.status AS status_estoque,re.observacao AS obs_estoque
            FROM prescricao p LEFT JOIN retorno_estoque re ON re.id_prescricao=p.id
            WHERE p.id_atendimento=%s ORDER BY p.data_prescricao,p.hora_prescricao""",(id_atend,))
        return cur.fetchall()
    finally:
        cur.close(); db.close()

def prescricoes_sem_retorno(id_atend):
    """Retorna prescrições que ainda não têm resposta do Estoque."""
    db=get_db(); cur=get_cur(db)
    try:
        cur.execute("""SELECT p.id,p.codigo_med,p.quantidade
            FROM prescricao p LEFT JOIN retorno_estoque re ON re.id_prescricao=p.id
            WHERE p.id_atendimento=%s AND re.id IS NULL""",(id_atend,))
        return cur.fetchall()
    finally:
        cur.close(); db.close()


# Status financeiro

def salvar_status_financeiro(cpf,status_fin,qtd_pendencias,valor_pendente,
                              data_vencimento,permite_atendimento,observacao):
    db=get_db(); cur=db.cursor()
    try:
        cur.execute("""INSERT INTO status_financeiro(cpf_paciente,status_financeiro,
            qtd_pendencias,valor_total_pendente,data_vencimento,
            permite_atendimento,observacao)
            VALUES(%s,%s,%s,%s,%s,%s,%s)""",
            (cpf,status_fin,qtd_pendencias,valor_pendente,
             data_vencimento,permite_atendimento,observacao or None))
        db.commit()
    finally:
        cur.close(); db.close()

def buscar_status_financeiro(cpf):
    db=get_db(); cur=get_cur(db)
    try:
        cur.execute("""SELECT * FROM status_financeiro WHERE cpf_paciente=%s
            ORDER BY consultado_em DESC LIMIT 1""",(cpf,))
        return cur.fetchone()
    finally:
        cur.close(); db.close()


# Retorno estoque

def salvar_retorno_estoque(id_prescricao,codigo_med,status,observacao=None):
    db=get_db(); cur=db.cursor()
    try:
        cur.execute("""INSERT INTO retorno_estoque(id_prescricao,codigo_med,status,observacao)
            VALUES(%s,%s,%s,%s)""",(id_prescricao,codigo_med,status,observacao or None))
        db.commit()
    finally:
        cur.close(); db.close()

