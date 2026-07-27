'use strict';

const { PAYMENT_STATUS, APPROVED_CARD_PREFIX, CARD } = require('../config/constants');

/** Mostra apenas os últimos dígitos — o legado logava o cartão inteiro. */
function maskCard(card) {
    const digits = String(card);
    return `${'*'.repeat(Math.max(digits.length - CARD.VISIBLE_DIGITS, 0))}${digits.slice(-CARD.VISIBLE_DIGITS)}`;
}

/**
 * Adapter do gateway de pagamento.
 *
 * A regra que decidia PAID/DENIED estava inline no handler HTTP do checkout.
 * Aqui ela fica isolada e substituível: trocar por um gateway real significa
 * implementar `charge()` em outra classe e injetá-la na composition root.
 *
 * A chave da API é recebida por injeção (vem de `process.env`) e **nunca**
 * aparece em log.
 */
class PaymentGateway {
    constructor({ apiKey, logger = console } = {}) {
        if (!apiKey) {
            throw new Error('PaymentGateway exige uma apiKey (PAYMENT_GATEWAY_KEY)');
        }
        this.apiKey = apiKey;
        this.logger = logger;
    }

    /** Simulação: cartões iniciados com "4" são aprovados. */
    async charge({ card, amount, courseId }) {
        this.logger.log(
            `[payment] cobrança de ${amount} referente ao curso ${courseId} no cartão ${maskCard(card)}`
        );

        const status = card.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
        return { status, amount, approved: status === PAYMENT_STATUS.PAID };
    }
}

module.exports = PaymentGateway;
