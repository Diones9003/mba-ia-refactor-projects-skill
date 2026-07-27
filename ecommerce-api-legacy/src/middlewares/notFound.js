'use strict';

const { MESSAGES } = require('../config/constants');
const { NotFoundError } = require('../errors');

/** Rotas não registradas caem aqui e seguem para o error handler central. */
const notFound = (req, res, next) => {
    next(new NotFoundError(MESSAGES.ROUTE_NOT_FOUND));
};

module.exports = notFound;
