'use strict';

const express = require('express');

const config = require('./config');
const Database = require('./database/connection');
const { initializeDatabase } = require('./database/schema');

const UserModel = require('./models/userModel');
const CourseModel = require('./models/courseModel');
const EnrollmentModel = require('./models/enrollmentModel');
const PaymentModel = require('./models/paymentModel');
const AuditLogModel = require('./models/auditLogModel');
const ReportModel = require('./models/reportModel');

const PasswordHasher = require('./services/passwordHasher');
const PaymentGateway = require('./services/paymentGateway');
const CacheService = require('./services/cacheService');
const CheckoutService = require('./services/checkoutService');
const ReportService = require('./services/reportService');
const UserService = require('./services/userService');

const CheckoutController = require('./controllers/checkoutController');
const ReportController = require('./controllers/reportController');
const UserController = require('./controllers/userController');

const checkoutRoutes = require('./views/checkoutRoutes');
const reportRoutes = require('./views/reportRoutes');
const userRoutes = require('./views/userRoutes');

const errorHandler = require('./middlewares/errorHandler');
const notFound = require('./middlewares/notFound');

/**
 * Composition root: monta o grafo de dependências e devolve o app Express.
 *
 * Toda dependência é **injetada** (banco, gateway, hasher, cache), de modo que
 * um teste possa substituir qualquer uma delas — no legado a classe `AppManager`
 * instanciava o próprio banco no construtor.
 */
function createApp({ db, passwordHasher, paymentGateway, cache, logger = console } = {}) {
    if (!db) throw new Error('createApp exige uma conexão de banco injetada');

    const app = express();
    app.use(express.json());

    const hasher = passwordHasher ?? new PasswordHasher();
    const gateway = paymentGateway ?? new PaymentGateway({ apiKey: config.paymentGateway.apiKey, logger });
    const checkoutCache = cache ?? new CacheService({ logger });

    const users = new UserModel(db);
    const courses = new CourseModel(db);
    const enrollments = new EnrollmentModel(db);
    const payments = new PaymentModel(db);
    const auditLogs = new AuditLogModel(db);
    const report = new ReportModel(db);

    const checkoutService = new CheckoutService({
        db,
        users,
        courses,
        enrollments,
        payments,
        auditLogs,
        paymentGateway: gateway,
        passwordHasher: hasher,
        cache: checkoutCache,
        logger
    });
    const reportService = new ReportService({ report });
    const userService = new UserService({ db, users, enrollments, payments });

    app.use(checkoutRoutes(new CheckoutController(checkoutService)));
    app.use(reportRoutes(new ReportController(reportService)));
    app.use(userRoutes(new UserController(userService)));

    app.use(notFound);
    app.use(errorHandler({ logger }));

    return app;
}

/** Abre a conexão, prepara o schema e devolve o app pronto para escutar. */
async function bootstrap({ logger = console } = {}) {
    const db = await Database.open(config.database.path);
    const passwordHasher = new PasswordHasher();

    await initializeDatabase(db, { seed: config.database.seed, passwordHasher, logger });

    const app = createApp({ db, passwordHasher, logger });
    return { app, db };
}

async function start({ port = config.port, logger = console } = {}) {
    const { app, db } = await bootstrap({ logger });

    const server = app.listen(port, () => {
        logger.log(`LMS API rodando na porta ${server.address().port}... (env: ${config.env})`);
    });

    const shutdown = async (signal) => {
        logger.log(`[app] ${signal} recebido, encerrando...`);
        server.close(async () => {
            await db.close().catch(() => {});
            process.exit(0);
        });
    };
    process.once('SIGINT', () => shutdown('SIGINT'));
    process.once('SIGTERM', () => shutdown('SIGTERM'));

    return { app, db, server };
}

if (require.main === module) {
    start().catch((error) => {
        console.error('[app] falha ao iniciar', error);
        process.exit(1);
    });
}

module.exports = { createApp, bootstrap, start };
