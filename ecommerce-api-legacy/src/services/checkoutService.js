'use strict';

const { MESSAGES, PAYMENT_STATUS } = require('../config/constants');
const { NotFoundError, PaymentDeclinedError, DatabaseError } = require('../errors');

/** Converte falha de infraestrutura na mensagem 500 usada pelo endpoint original. */
const asDatabaseError = (message) => (cause) => {
    throw new DatabaseError(message, { cause });
};

/**
 * Regra de negócio do checkout, extraída do handler `POST /api/checkout`.
 *
 * Responsabilidades: localizar o curso ativo, garantir o usuário, cobrar no
 * gateway e — de forma **atômica** — criar matrícula, pagamento e log de
 * auditoria. Não conhece `req`/`res`.
 */
class CheckoutService {
    constructor({
        db,
        users,
        courses,
        enrollments,
        payments,
        auditLogs,
        paymentGateway,
        passwordHasher,
        cache,
        logger = console
    }) {
        this.db = db;
        this.users = users;
        this.courses = courses;
        this.enrollments = enrollments;
        this.payments = payments;
        this.auditLogs = auditLogs;
        this.paymentGateway = paymentGateway;
        this.passwordHasher = passwordHasher;
        this.cache = cache;
        this.logger = logger;
    }

    async execute({ userName, email, password, courseId, card }) {
        const course = await this.courses
            .findActiveById(courseId)
            .catch(asDatabaseError(MESSAGES.DB_ERROR));

        if (!course) {
            throw new NotFoundError(MESSAGES.COURSE_NOT_FOUND);
        }

        const userId = await this.resolveUser({ userName, email, password });

        const payment = await this.paymentGateway.charge({ card, amount: course.price, courseId });
        if (payment.status === PAYMENT_STATUS.DENIED) {
            throw new PaymentDeclinedError();
        }

        const enrollmentId = await this.registerEnrollment({ userId, course, payment });

        this.rememberLastCheckout(userId, course.title);

        return { enrollmentId, userId, course };
    }

    /**
     * Devolve o id do usuário, criando-o quando o e-mail é novo.
     *
     * A criação acontece **antes** da cobrança, como no fluxo original: um
     * pagamento recusado ainda deixa a conta criada.
     */
    async resolveUser({ userName, email, password }) {
        const existing = await this.users.findByEmail(email).catch(asDatabaseError(MESSAGES.DB_ERROR));
        if (existing) return existing.id;

        // Sem senha informada, gera uma aleatória em vez da senha padrão fixa
        // que o código original atribuía nesse caso.
        const rawPassword = password || this.passwordHasher.generateRandomPassword();
        const passwordHash = await this.passwordHasher.hash(rawPassword);

        return this.users
            .create({ name: userName, email, passwordHash })
            .catch(asDatabaseError(MESSAGES.USER_CREATE_ERROR));
    }

    /** Matrícula + pagamento + auditoria em uma única transação (tudo ou nada). */
    registerEnrollment({ userId, course, payment }) {
        return this.db.transaction(async () => {
            const enrollmentId = await this.enrollments
                .create({ userId, courseId: course.id })
                .catch(asDatabaseError(MESSAGES.ENROLLMENT_ERROR));

            await this.payments
                .create({ enrollmentId, amount: payment.amount, status: payment.status })
                .catch(asDatabaseError(MESSAGES.PAYMENT_ERROR));

            await this.auditLogs
                .record(`Checkout curso ${course.id} por ${userId}`)
                .catch(asDatabaseError(MESSAGES.AUDIT_ERROR));

            return enrollmentId;
        });
    }

    /** Cache é best-effort: uma falha aqui não invalida o checkout já efetuado. */
    rememberLastCheckout(userId, courseTitle) {
        try {
            this.cache.set(`last_checkout_${userId}`, courseTitle);
        } catch (error) {
            this.logger.warn?.('[cache] falha ao gravar último checkout', error);
        }
    }
}

module.exports = CheckoutService;
