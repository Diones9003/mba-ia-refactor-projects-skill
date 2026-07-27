'use strict';

const { MESSAGES } = require('./config/constants');

/**
 * Erros de domínio da aplicação.
 *
 * Services e models lançam estes erros; nenhum deles conhece `res`. O
 * middleware `errorHandler` é o único ponto que traduz erro → resposta HTTP.
 */
class AppError extends Error {
    constructor(message, status, options = {}) {
        super(message, options);
        this.name = this.constructor.name;
        this.status = status;
        Error.captureStackTrace?.(this, this.constructor);
    }
}

class ValidationError extends AppError {
    constructor(message = MESSAGES.BAD_REQUEST, options) {
        super(message, 400, options);
    }
}

class NotFoundError extends AppError {
    constructor(message, options) {
        super(message, 404, options);
    }
}

/** Pagamento recusado pelo gateway — regra de negócio, não falha técnica. */
class PaymentDeclinedError extends AppError {
    constructor(message = MESSAGES.PAYMENT_DECLINED, options) {
        super(message, 400, options);
    }
}

/** Falha de infraestrutura de dados; preserva as mensagens 500 do legado. */
class DatabaseError extends AppError {
    constructor(message = MESSAGES.DB_ERROR, options) {
        super(message, 500, options);
    }
}

module.exports = {
    AppError,
    ValidationError,
    NotFoundError,
    PaymentDeclinedError,
    DatabaseError
};
