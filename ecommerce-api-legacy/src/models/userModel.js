'use strict';

/** Acesso a dados da entidade `users`. Não conhece HTTP nem regra de negócio. */
class UserModel {
    constructor(db) {
        this.db = db;
    }

    findById(id) {
        return this.db.get('SELECT id, name, email FROM users WHERE id = ?', [id]);
    }

    findByEmail(email) {
        return this.db.get('SELECT id, name, email FROM users WHERE email = ?', [email]);
    }

    async create({ name, email, passwordHash }) {
        if (!name || !email || !passwordHash) {
            throw new Error('UserModel.create exige name, email e passwordHash');
        }
        const { lastID } = await this.db.run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            [name, email, passwordHash]
        );
        return lastID;
    }

    async deleteById(id) {
        const { changes } = await this.db.run('DELETE FROM users WHERE id = ?', [id]);
        return changes;
    }
}

module.exports = UserModel;
