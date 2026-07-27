'use strict';

const sqlite3 = require('sqlite3');

/**
 * Adapter fino sobre o driver `sqlite3`, expondo uma API baseada em Promises.
 *
 * Existe para que models usem `await` em vez dos callbacks aninhados do driver
 * (a origem do "callback hell" e do truque `const self = this` no código legado)
 * e para que a conexão possa ser **injetada** nos models em vez de instanciada
 * dentro deles.
 */
class Database {
    constructor(driver) {
        this.driver = driver;
    }

    /** Abre a conexão. A composition root chama isto uma única vez. */
    static open(filename) {
        return new Promise((resolve, reject) => {
            const driver = new sqlite3.Database(filename, (err) => {
                if (err) return reject(err);
                resolve(new Database(driver));
            });
        });
    }

    /** Executa INSERT/UPDATE/DELETE/DDL e devolve `{ lastID, changes }`. */
    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.driver.run(sql, params, function (err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    /** Primeira linha do resultado (ou `undefined`). */
    get(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.driver.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
        });
    }

    /** Todas as linhas do resultado. */
    all(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.driver.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows || [])));
        });
    }

    /**
     * Executa `work()` dentro de uma transação, com rollback em caso de erro.
     * Garante que escritas relacionadas (matrícula + pagamento + auditoria)
     * sejam atômicas — no legado elas eram inserts independentes.
     */
    async transaction(work) {
        await this.run('BEGIN');
        try {
            const result = await work();
            await this.run('COMMIT');
            return result;
        } catch (error) {
            await this.run('ROLLBACK').catch(() => {});
            throw error;
        }
    }

    close() {
        return new Promise((resolve, reject) => {
            this.driver.close((err) => (err ? reject(err) : resolve()));
        });
    }
}

module.exports = Database;
