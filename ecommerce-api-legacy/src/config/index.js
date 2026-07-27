'use strict';

const path = require('path');

require('dotenv').config({ path: path.resolve(__dirname, '..', '..', '.env'), quiet: true });

/** Falha no boot (fail fast) quando um segredo obrigatório não foi provido. */
function required(name) {
    const value = process.env[name];
    if (!value) {
        throw new Error(
            `Variável de ambiente obrigatória ausente: ${name}. ` +
            'Copie .env.example para .env e preencha os valores.'
        );
    }
    return value;
}

function optional(name, fallback) {
    const value = process.env[name];
    return value === undefined || value === '' ? fallback : value;
}

function asInteger(name, fallback) {
    const parsed = Number.parseInt(optional(name, String(fallback)), 10);
    if (!Number.isInteger(parsed)) {
        throw new Error(`Variável de ambiente ${name} deve ser um número inteiro.`);
    }
    return parsed;
}

function asBoolean(name, fallback) {
    return optional(name, String(fallback)).toLowerCase() === 'true';
}

/**
 * Configuração única da aplicação, lida exclusivamente do ambiente.
 * Nenhum segredo é literal no código-fonte (ver `.env.example`).
 */
const config = Object.freeze({
    env: optional('NODE_ENV', 'development'),
    port: asInteger('PORT', 3000),

    database: Object.freeze({
        path: optional('DATABASE_PATH', ':memory:'),
        seed: asBoolean('SEED_DATABASE', true)
    }),

    paymentGateway: Object.freeze({
        apiKey: required('PAYMENT_GATEWAY_KEY')
    }),

    smtp: Object.freeze({
        user: optional('SMTP_USER', '')
    })
});

module.exports = config;
