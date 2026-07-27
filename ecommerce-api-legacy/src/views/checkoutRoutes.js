'use strict';

const { Router } = require('express');

const asyncHandler = require('../middlewares/asyncHandler');
const { validateBody } = require('../middlewares/validate');

/**
 * Contrato de entrada de `POST /api/checkout`.
 *
 * As chaves são os nomes **da API** (mantidos por compatibilidade) e `as` é o
 * nome interno descritivo entregue ao controller.
 */
const CHECKOUT_SCHEMA = {
    usr: { as: 'userName', rule: 'text' },
    eml: { as: 'email', rule: 'email' },
    pwd: { as: 'password', rule: 'password', optional: true },
    c_id: { as: 'courseId', rule: 'positiveInteger' },
    card: { as: 'card', rule: 'cardNumber' }
};

module.exports = (checkoutController) => {
    const router = Router();

    router.post('/api/checkout', validateBody(CHECKOUT_SCHEMA), asyncHandler(checkoutController.create));

    return router;
};

module.exports.CHECKOUT_SCHEMA = CHECKOUT_SCHEMA;
