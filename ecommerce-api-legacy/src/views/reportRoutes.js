'use strict';

const { Router } = require('express');

const asyncHandler = require('../middlewares/asyncHandler');

module.exports = (reportController) => {
    const router = Router();

    router.get('/api/admin/financial-report', asyncHandler(reportController.financial));

    return router;
};
