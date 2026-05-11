-- =============================================================================
-- banco.sql — Schema PostgreSQL da Entrega 4 (Integração REST)
-- Banco: db_atendimento_rest
-- Independente dos bancos das Entregas 2 e 3.
-- =============================================================================

-- CREATE DATABASE db_atendimento_rest;
-- \c db_atendimento_rest

-- -----------------------------------------------------------------------------
-- PACIENTE
-- -----------------------------------------------------------------------------
CREATE TABLE paciente (
    cpf         CHAR(11)     PRIMARY KEY,
    nome        VARCHAR(100) NOT NULL,
    data_nasc   DATE,
    telefone    VARCHAR(20),
    email       VARCHAR(100)
);

-- -----------------------------------------------------------------------------
-- ATENDIMENTO
-- -----------------------------------------------------------------------------
CREATE TABLE atendimento (
    id               BIGSERIAL    PRIMARY KEY,
    cpf_paciente     CHAR(11)     NOT NULL REFERENCES paciente(cpf),
    crm_medico       VARCHAR(15),
    tipo             VARCHAR(20)  NOT NULL
                     CHECK(tipo IN ('CONSULTA','RETORNO','INTERNACAO','EMERGENCIA')),
    convenio         VARCHAR(60),
    carteirinha      VARCHAR(30),
    data_abertura    DATE         NOT NULL DEFAULT CURRENT_DATE,
    hora_abertura    TIME         NOT NULL DEFAULT CURRENT_TIME,
    status           VARCHAR(12)  NOT NULL DEFAULT 'ABERTO'
                     CHECK(status IN ('ABERTO','FINALIZADO')),
    cid              VARCHAR(10),
    codigo_tuss      VARCHAR(20),
    valor_total      NUMERIC(10,2),
    data_finalizacao DATE,
    hora_finalizacao TIME,
    observacoes      TEXT
);

-- -----------------------------------------------------------------------------
-- PRESCRICAO
-- -----------------------------------------------------------------------------
CREATE TABLE prescricao (
    id              BIGSERIAL    PRIMARY KEY,
    id_atendimento  BIGINT       NOT NULL REFERENCES atendimento(id),
    cpf_paciente    CHAR(11)     NOT NULL REFERENCES paciente(cpf),
    crm_medico      VARCHAR(15),
    codigo_med      BIGINT       NOT NULL,
    quantidade      NUMERIC(8,3) NOT NULL CHECK(quantidade > 0),
    unidade         CHAR(4)      NOT NULL,
    instrucoes      TEXT,
    data_prescricao DATE         NOT NULL DEFAULT CURRENT_DATE,
    hora_prescricao TIME         NOT NULL DEFAULT CURRENT_TIME
);

-- -----------------------------------------------------------------------------
-- STATUS_FINANCEIRO
-- Populado via REST pelo Financeiro (GET /api/pacientes/<cpf>/status-financeiro).
-- Mesma lógica da Entrega 3 — sempre INSERT, consulta o mais recente.
-- -----------------------------------------------------------------------------
CREATE TABLE status_financeiro (
    id                   BIGSERIAL     PRIMARY KEY,
    cpf_paciente         CHAR(11)      NOT NULL REFERENCES paciente(cpf),
    status_financeiro    VARCHAR(10)   NOT NULL
                         CHECK(status_financeiro IN ('REGULAR','PENDENTE','BLOQUEADO')),
    qtd_pendencias       INTEGER       NOT NULL DEFAULT 0,
    valor_total_pendente NUMERIC(12,2) NOT NULL DEFAULT 0,
    data_vencimento      DATE,
    permite_atendimento  CHAR(1)       NOT NULL
                         CHECK(permite_atendimento IN ('S','N','E')),
    observacao           TEXT,
    consultado_em        TIMESTAMP     NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- RETORNO_ESTOQUE
-- Populado via resposta síncrona do Estoque ao POST /api/prescricoes.
-- Na Entrega 4 não há etapa de "confirmar reserva" separada —
-- o Estoque responde na mesma chamada REST.
-- -----------------------------------------------------------------------------
CREATE TABLE retorno_estoque (
    id              BIGSERIAL    PRIMARY KEY,
    id_prescricao   BIGINT       NOT NULL REFERENCES prescricao(id),
    codigo_med      BIGINT       NOT NULL,
    status          VARCHAR(20)  NOT NULL
                    CHECK(status IN ('DISPONIVEL','SEPARADO','ENTREGUE',
                                     'INDISPONIVEL','ERRO')),
    observacao      TEXT,
    respondido_em   TIMESTAMP    NOT NULL DEFAULT NOW()
);


