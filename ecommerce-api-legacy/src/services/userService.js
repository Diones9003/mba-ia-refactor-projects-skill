'use strict';

const { MESSAGES } = require('../config/constants');
const { AppError, NotFoundError, DatabaseError } = require('../errors');

/**
 * Regra de negócio de usuários.
 *
 * A remoção agora é consistente: pagamentos → matrículas → usuário, na mesma
 * transação. O endpoint original apagava apenas o usuário e a própria resposta
 * admitia que matrículas e pagamentos ficavam órfãos no banco.
 */
class UserService {
    constructor({ db, users, enrollments, payments }) {
        this.db = db;
        this.users = users;
        this.enrollments = enrollments;
        this.payments = payments;
    }

    async remove(userId) {
        const user = await this.users.findById(userId).catch((cause) => {
            throw new DatabaseError(MESSAGES.DB_ERROR, { cause });
        });

        if (!user) {
            throw new NotFoundError(MESSAGES.USER_NOT_FOUND);
        }

        return this.db
            .transaction(async () => {
                const removedPayments = await this.payments.deleteByUserId(userId);
                const removedEnrollments = await this.enrollments.deleteByUserId(userId);
                await this.users.deleteById(userId);

                return { userId, removedEnrollments, removedPayments };
            })
            .catch((cause) => {
                if (cause instanceof AppError) throw cause;
                throw new DatabaseError(MESSAGES.DB_ERROR, { cause });
            });
    }
}

module.exports = UserService;
