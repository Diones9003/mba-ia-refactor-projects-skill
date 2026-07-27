'use strict';

/** Acesso a dados da entidade `audit_logs`. */
class AuditLogModel {
    constructor(db) {
        this.db = db;
    }

    async record(action) {
        const { lastID } = await this.db.run(
            "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
            [action]
        );
        return lastID;
    }
}

module.exports = AuditLogModel;
