'use strict';

const { MESSAGES, PAYMENT_STATUS } = require('../config/constants');
const { DatabaseError } = require('../errors');

const UNKNOWN_STUDENT = 'Unknown';

/**
 * Agregação do relatório financeiro.
 *
 * O legado montava o relatório com queries aninhadas e contadores manuais
 * (`coursesPending`/`enrPending`) para saber quando responder. Aqui o model
 * devolve as linhas de uma única query com JOIN e a agregação é feita em
 * memória, de forma determinística.
 */
class ReportService {
    constructor({ report }) {
        this.report = report;
    }

    async financialReport() {
        const rows = await this.report.financialSummaryRows().catch((cause) => {
            throw new DatabaseError(MESSAGES.DB_ERROR, { cause });
        });

        const courses = new Map();
        const countedEnrollments = new Set();

        for (const row of rows) {
            if (!courses.has(row.course_id)) {
                courses.set(row.course_id, { title: row.course_title, revenue: 0, students: [] });
            }
            const course = courses.get(row.course_id);

            // LEFT JOIN sem matrícula: o curso entra no relatório sem alunos.
            if (row.enrollment_id === null) continue;

            // Só a primeira linha de cada matrícula conta, espelhando o
            // `db.get` do legado, que lia um único pagamento por matrícula.
            if (countedEnrollments.has(row.enrollment_id)) continue;
            countedEnrollments.add(row.enrollment_id);

            const amount = row.payment_amount ?? 0;
            if (row.payment_status === PAYMENT_STATUS.PAID) {
                course.revenue += amount;
            }

            course.students.push({
                name: row.student_name ?? UNKNOWN_STUDENT,
                paid: amount
            });
        }

        return [...courses.values()];
    }
}

module.exports = ReportService;
