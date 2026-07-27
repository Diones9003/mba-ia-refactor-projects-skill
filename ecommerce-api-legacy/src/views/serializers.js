'use strict';

const { MESSAGES } = require('../config/constants');

/**
 * Serialização das respostas (camada View de uma API REST).
 *
 * Centraliza a montagem do JSON que antes era feita à mão dentro de cada
 * handler. Os formatos abaixo são **exatamente** os dos endpoints originais.
 */

/** `{ "msg": "Sucesso", "enrollment_id": 2 }` */
const checkoutCreated = ({ enrollmentId }) => ({
    msg: MESSAGES.CHECKOUT_SUCCESS,
    enrollment_id: enrollmentId
});

/** `[{ "course": "Docker", "revenue": 497, "students": [{ "student": "...", "paid": 497 }] }]` */
const financialReport = (courses) =>
    courses.map((course) => ({
        course: course.title,
        revenue: course.revenue,
        students: course.students.map((student) => ({
            student: student.name,
            paid: student.paid
        }))
    }));

/** Resposta em texto do DELETE, como no endpoint original. */
const userDeleted = () => MESSAGES.USER_DELETED;

module.exports = { checkoutCreated, financialReport, userDeleted };
