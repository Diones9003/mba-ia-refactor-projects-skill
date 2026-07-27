'use strict';

/**
 * Encaminha rejeições de handlers `async` para o middleware de erro.
 *
 * Sem isto, o Express 4 não captura promises rejeitadas e a request ficaria
 * pendurada — era esse buraco que fazia cada handler do legado tratar erro na
 * mão (e, em vários pontos, ignorá-lo).
 */
const asyncHandler = (handler) => (req, res, next) => {
    Promise.resolve(handler(req, res, next)).catch(next);
};

module.exports = asyncHandler;
