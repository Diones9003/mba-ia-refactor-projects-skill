'use strict';

const { CARD, MESSAGES } = require('../config/constants');
const { ValidationError } = require('../errors');

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * Regras reutilizáveis. Cada regra devolve o valor **normalizado** ou
 * `undefined` quando a entrada é inválida.
 */
const RULES = {
    text: (value) => (typeof value === 'string' && value.trim() !== '' ? value.trim() : undefined),

    email: (value) => {
        const email = typeof value === 'string' ? value.trim() : '';
        return EMAIL_PATTERN.test(email) ? email : undefined;
    },

    password: (value) => (typeof value === 'string' && value !== '' ? value : undefined),

    positiveInteger: (value) => {
        const parsed = Number(value);
        return Number.isInteger(parsed) && parsed > 0 ? parsed : undefined;
    },

    cardNumber: (value) => {
        const card = typeof value === 'string' ? value.trim() : '';
        const onlyDigits = /^\d+$/.test(card);
        const withinRange = card.length >= CARD.MIN_DIGITS && card.length <= CARD.MAX_DIGITS;
        return onlyDigits && withinRange ? card : undefined;
    }
};

/**
 * Valida o corpo da request contra um schema declarativo (Padrão 7).
 *
 * O schema mapeia o **nome do campo na API** (preservado por contrato: `usr`,
 * `eml`, `c_id`…) para um nome interno descritivo, eliminando as variáveis
 * `u`/`e`/`p`/`cc` do handler original.
 */
const validateBody = (schema) => (req, res, next) => {
    const body = req.body ?? {};
    const validated = {};

    for (const [field, spec] of Object.entries(schema)) {
        const raw = body[field];

        if (raw === undefined || raw === null || raw === '') {
            if (spec.optional) continue;
            return next(new ValidationError(MESSAGES.BAD_REQUEST));
        }

        const value = RULES[spec.rule](raw);
        if (value === undefined) {
            return next(new ValidationError(MESSAGES.BAD_REQUEST));
        }
        validated[spec.as] = value;
    }

    req.validated = { ...req.validated, body: validated };
    next();
};

/** Valida um parâmetro de rota numérico (ex.: `/api/users/:id`). */
const validateIdParam = (param = 'id', as = param) => (req, res, next) => {
    const value = RULES.positiveInteger(req.params[param]);
    if (value === undefined) {
        return next(new ValidationError(MESSAGES.BAD_REQUEST));
    }

    req.validated = { ...req.validated, params: { ...req.validated?.params, [as]: value } };
    next();
};

module.exports = { validateBody, validateIdParam, RULES };
