'use strict';

/** Acesso a dados da entidade `enrollments` (matrículas). */
class EnrollmentModel {
    constructor(db) {
        this.db = db;
    }

    async create({ userId, courseId }) {
        const { lastID } = await this.db.run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
            [userId, courseId]
        );
        return lastID;
    }

    /** Remoção em lote sem N+1: uma única query por usuário. */
    async deleteByUserId(userId) {
        const { changes } = await this.db.run('DELETE FROM enrollments WHERE user_id = ?', [userId]);
        return changes;
    }
}

module.exports = EnrollmentModel;
