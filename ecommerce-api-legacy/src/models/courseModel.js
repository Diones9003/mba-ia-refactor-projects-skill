'use strict';

/** Acesso a dados da entidade `courses`. */
class CourseModel {
    constructor(db) {
        this.db = db;
    }

    /** Somente cursos ativos podem ser comprados (regra do checkout original). */
    findActiveById(id) {
        return this.db.get('SELECT id, title, price, active FROM courses WHERE id = ? AND active = 1', [id]);
    }
}

module.exports = CourseModel;
