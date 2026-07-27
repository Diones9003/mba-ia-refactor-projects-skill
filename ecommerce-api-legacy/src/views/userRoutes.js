'use strict';

const { Router } = require('express');

const asyncHandler = require('../middlewares/asyncHandler');
const { validateIdParam } = require('../middlewares/validate');

module.exports = (userController) => {
    const router = Router();

    router.delete('/api/users/:id', validateIdParam('id'), asyncHandler(userController.remove));

    return router;
};
