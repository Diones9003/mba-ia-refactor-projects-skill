'use strict';

const serializers = require('../views/serializers');

/** Orquestra o fluxo de `GET /api/admin/financial-report`. */
class ReportController {
    constructor(reportService) {
        this.reportService = reportService;
    }

    financial = async (req, res) => {
        const courses = await this.reportService.financialReport();
        res.status(200).json(serializers.financialReport(courses));
    };
}

module.exports = ReportController;
