'use strict';

const { MESSAGES } = require('../config/constants');
const { AppError } = require('../errors');

/**
 * Error handling centralizado (Padrão 5).
 *
 * Único ponto que traduz erro → resposta HTTP. Substitui os
 * `res.status(500).send("Erro DB")` repetidos em cada callback do legado — e,
 * principalmente, os callbacks que ignoravam `err` e respondiam sucesso.
 *
 * O corpo é enviado como texto (`res.send`) para preservar o formato das
 * respostas de erro dos endpoints originais.
 */
const errorHandler = ({ logger = console } = {}) => (err, req, res, next) => {
    if (res.headersSent) return next(err);

    // AppError traz o status; erros do próprio Express (ex.: JSON malformado
    // rejeitado por express.json) trazem `status`/`statusCode`.
    const status = err.status ?? err.statusCode ?? 500;
    const message = err instanceof AppError
        ? err.message
        : status < 500
            ? MESSAGES.BAD_REQUEST
            : MESSAGES.INTERNAL_ERROR;

    const context = `${req.method} ${req.originalUrl} -> ${status}`;
    if (status >= 500) {
        logger.error(`[error] ${context}`, err);
    } else {
        (logger.warn ?? logger.log)(`[warn] ${context}: ${message}`);
    }

    res.status(status).send(message);
};

module.exports = errorHandler;
