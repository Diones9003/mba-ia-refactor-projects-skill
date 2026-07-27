'use strict';

/**
 * Consultas do relatório financeiro.
 *
 * Substitui o N+1 do legado (1 query de cursos + 1 por curso + 2 por matrícula)
 * por **uma única** query com LEFT JOINs. Os LEFT JOINs preservam o
 * comportamento original de listar também cursos sem matrículas e matrículas
 * sem pagamento ou sem usuário.
 */
const FINANCIAL_SUMMARY_SQL = `
    SELECT
        c.id            AS course_id,
        c.title         AS course_title,
        e.id            AS enrollment_id,
        u.name          AS student_name,
        p.id            AS payment_id,
        p.amount        AS payment_amount,
        p.status        AS payment_status
    FROM courses c
    LEFT JOIN enrollments e ON e.course_id = c.id
    LEFT JOIN users       u ON u.id = e.user_id
    LEFT JOIN payments    p ON p.enrollment_id = e.id
    ORDER BY c.id, e.id, p.id
`;

class ReportModel {
    constructor(db) {
        this.db = db;
    }

    /** Linhas achatadas curso × matrícula × pagamento, em ordem determinística. */
    financialSummaryRows() {
        return this.db.all(FINANCIAL_SUMMARY_SQL);
    }
}

module.exports = ReportModel;
