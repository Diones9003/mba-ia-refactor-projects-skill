'use strict';

const { PAYMENT_STATUS } = require('../config/constants');

/**
 * Schema e seeds. Antes ficavam dentro de `AppManager.initDb`, misturados com
 * roteamento e regra de negócio.
 *
 * Diferença em relação ao legado: as chaves estrangeiras agora são declaradas e
 * o `PRAGMA foreign_keys` é habilitado, de modo que o banco também rejeite os
 * registros órfãos que o `DELETE /api/users/:id` original deixava para trás.
 */
const TABLES = [
    `CREATE TABLE IF NOT EXISTS users (
        id    INTEGER PRIMARY KEY,
        name  TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        pass  TEXT NOT NULL
    )`,
    `CREATE TABLE IF NOT EXISTS courses (
        id     INTEGER PRIMARY KEY,
        title  TEXT NOT NULL,
        price  REAL NOT NULL,
        active INTEGER NOT NULL DEFAULT 1
    )`,
    `CREATE TABLE IF NOT EXISTS enrollments (
        id        INTEGER PRIMARY KEY,
        user_id   INTEGER NOT NULL REFERENCES users(id),
        course_id INTEGER NOT NULL REFERENCES courses(id)
    )`,
    `CREATE TABLE IF NOT EXISTS payments (
        id            INTEGER PRIMARY KEY,
        enrollment_id INTEGER NOT NULL REFERENCES enrollments(id),
        amount        REAL NOT NULL,
        status        TEXT NOT NULL
    )`,
    `CREATE TABLE IF NOT EXISTS audit_logs (
        id         INTEGER PRIMARY KEY,
        action     TEXT NOT NULL,
        created_at DATETIME NOT NULL
    )`
];

const INDEXES = [
    'CREATE INDEX IF NOT EXISTS idx_enrollments_user ON enrollments(user_id)',
    'CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id)',
    'CREATE INDEX IF NOT EXISTS idx_payments_enrollment ON payments(enrollment_id)'
];

/** Dados de desenvolvimento idênticos aos do boot original. */
const SEED = Object.freeze({
    user: { name: 'Leonan', email: 'leonan@fullcycle.com.br', password: '123' },
    courses: [
        { title: 'Clean Architecture', price: 997.0, active: 1 },
        { title: 'Docker', price: 497.0, active: 1 }
    ],
    enrollment: { userId: 1, courseId: 1 },
    payment: { enrollmentId: 1, amount: 997.0, status: PAYMENT_STATUS.PAID }
});

async function createSchema(db) {
    await db.run('PRAGMA foreign_keys = ON');
    for (const statement of TABLES) {
        await db.run(statement);
    }
    for (const statement of INDEXES) {
        await db.run(statement);
    }
}

async function isEmpty(db) {
    const row = await db.get('SELECT COUNT(*) AS total FROM users');
    return row.total === 0;
}

/**
 * Popula o banco de desenvolvimento. Diferente do legado, a senha do usuário
 * de seed é gravada com hash — nada de senha em texto puro no banco.
 */
async function seedDatabase(db, { passwordHasher }) {
    const passwordHash = await passwordHasher.hash(SEED.user.password);

    await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [
        SEED.user.name,
        SEED.user.email,
        passwordHash
    ]);

    for (const course of SEED.courses) {
        await db.run('INSERT INTO courses (title, price, active) VALUES (?, ?, ?)', [
            course.title,
            course.price,
            course.active
        ]);
    }

    await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [
        SEED.enrollment.userId,
        SEED.enrollment.courseId
    ]);

    await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [
        SEED.payment.enrollmentId,
        SEED.payment.amount,
        SEED.payment.status
    ]);
}

async function initializeDatabase(db, { seed = false, passwordHasher, logger = console } = {}) {
    await createSchema(db);

    if (seed && (await isEmpty(db))) {
        await seedDatabase(db, { passwordHasher });
        logger.log('[db] schema criado e seeds aplicados');
        return;
    }

    logger.log('[db] schema criado');
}

module.exports = { initializeDatabase, createSchema, seedDatabase, SEED };
