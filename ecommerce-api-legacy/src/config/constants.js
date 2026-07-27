'use strict';

/**
 * Constantes de domínio e mensagens da API.
 *
 * Substitui os magic numbers/strings que estavam espalhados pelo código legado
 * (prefixo de cartão aprovado, status de pagamento, o loop de 10.000 iterações
 * do hash caseiro e as mensagens de resposta duplicadas em cada handler).
 */

const PAYMENT_STATUS = Object.freeze({
    PAID: 'PAID',
    DENIED: 'DENIED'
});

/** Regra do gateway simulado: cartões iniciados com "4" são aprovados. */
const APPROVED_CARD_PREFIX = '4';

const CARD = Object.freeze({
    MIN_DIGITS: 13,
    MAX_DIGITS: 19,
    VISIBLE_DIGITS: 4
});

/** Parâmetros do scrypt que substituiu a função `badCrypto`. */
const PASSWORD_HASH = Object.freeze({
    ALGORITHM: 'scrypt',
    SALT_BYTES: 16,
    KEY_LENGTH: 64,
    GENERATED_PASSWORD_BYTES: 32
});

/** Limite do cache em memória, que antes era um objeto global sem invalidação. */
const CACHE_MAX_ENTRIES = 500;

/**
 * Mensagens de resposta. As marcadas como "legado" são reproduzidas
 * literalmente para preservar o contrato dos endpoints originais.
 */
const MESSAGES = Object.freeze({
    BAD_REQUEST: 'Bad Request',                             // legado
    COURSE_NOT_FOUND: 'Curso não encontrado',               // legado
    PAYMENT_DECLINED: 'Pagamento recusado',                 // legado
    CHECKOUT_SUCCESS: 'Sucesso',                            // legado
    DB_ERROR: 'Erro DB',                                    // legado
    ENROLLMENT_ERROR: 'Erro Matrícula',                     // legado
    PAYMENT_ERROR: 'Erro Pagamento',                        // legado
    USER_CREATE_ERROR: 'Erro ao criar usuário',             // legado
    AUDIT_ERROR: 'Erro Auditoria',
    USER_NOT_FOUND: 'Usuário não encontrado',
    USER_DELETED: 'Usuário deletado. Matrículas e pagamentos associados foram removidos na mesma transação.',
    ROUTE_NOT_FOUND: 'Rota não encontrada',
    INTERNAL_ERROR: 'Erro interno'
});

module.exports = {
    PAYMENT_STATUS,
    APPROVED_CARD_PREFIX,
    CARD,
    PASSWORD_HASH,
    CACHE_MAX_ENTRIES,
    MESSAGES
};
