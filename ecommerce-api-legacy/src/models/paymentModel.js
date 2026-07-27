'use strict';

const { PAYMENT_STATUS } = require('../config/constants');

const VALID_STATUSES = Object.values(PAYMENT_STATUS);

/** Acesso a dados da entidade `payments`, com validação de invariantes. */
class PaymentModel {
    constructor(db) {
        this.db = db;
    }

    async create({ enrollmentId, amount, status }) {
        if (!VALID_STATUSES.includes(status)) {
            throw new Error(`Status de pagamento inválido: ${status}`);
        }
        if (typeof amount !== 'number' || Number.isNaN(amount) || amount < 0) {
            throw new Error(`Valor de pagamento inválido: ${amount}`);
        }

        const { lastID } = await this.db.run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollmentId, amount, status]
        );
        return lastID;
    }

    /**
     * Remove os pagamentos das matrículas de um usuário em uma só query
     * (subselect em vez de um DELETE por matrícula).
     */
    async deleteByUserId(userId) {
        const { changes } = await this.db.run(
            'DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)',
            [userId]
        );
        return changes;
    }
}

module.exports = PaymentModel;
